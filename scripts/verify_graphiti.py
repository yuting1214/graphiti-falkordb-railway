#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.9"]
# ///
"""
End-to-end verification for a deployed Graphiti + FalkorDB MCP server.

It connects to the live MCP endpoint over HTTP, writes a small episode (which
triggers LLM entity-extraction + embeddings + a FalkorDB write), waits for the
background processing to finish, then searches the graph to confirm the
extracted nodes/facts came back. Proves the *whole* stack, including the LLM key.

Usage:
    uv run scripts/verify_graphiti.py https://<your-graphiti-domain>
    # or:  python scripts/verify_graphiti.py https://<your-graphiti-domain>

Find <your-graphiti-domain> in Railway: graphiti service -> Settings ->
Networking -> the public domain (e.g. graphiti-production-xxxx.up.railway.app).
A trailing /mcp/ is added automatically.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def _mcp_url(base: str) -> str:
    # Target /mcp WITHOUT a trailing slash: on Railway the `/mcp/` form 307-redirects
    # to an (insecure) http://…/mcp which breaks the client. /mcp is served directly.
    base = base.strip().rstrip("/")
    if not base.startswith("http"):
        base = "https://" + base
    if base.endswith("/mcp"):
        return base
    return base + "/mcp"


def _text(result) -> str:
    """Flatten a CallToolResult's content into a string."""
    out = []
    for c in getattr(result, "content", []) or []:
        t = getattr(c, "text", None)
        out.append(t if t is not None else str(c))
    return "\n".join(out).strip()


def _pick(tools, *needles):
    """Find a tool whose name contains all needles (case-insensitive)."""
    for t in tools:
        n = t.name.lower()
        if all(x in n for x in needles):
            return t.name
    return None


async def main(base_url: str) -> int:
    url = _mcp_url(base_url)
    group_id = f"verify-{int(time.time())}"
    print(f"→ connecting to {url}")

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            names = [t.name for t in tools]
            print(f"✓ connected. {len(names)} tools: {', '.join(names)}\n")

            add = _pick(tools, "add", "memory") or _pick(tools, "add", "episode")
            snodes = _pick(tools, "search", "node")
            sfacts = _pick(tools, "search", "fact")
            getep = _pick(tools, "get", "episode")
            if not add:
                print("✗ no add_memory/add_episode tool exposed — cannot verify.")
                return 2

            # 1) write an episode with two clear, linkable facts
            episode = (
                "Ada Lovelace was a mathematician who worked with Charles Babbage "
                "on the Analytical Engine in London. She is regarded as the first "
                "computer programmer."
            )
            print(f"→ add_memory (group_id={group_id}) via '{add}' ...")
            r = await session.call_tool(
                add,
                {
                    "name": "verify-episode",
                    "episode_body": episode,
                    "group_id": group_id,
                    "source": "text",
                    "source_description": "graphiti template verification",
                },
            )
            print(f"  {_text(r)[:200] or '(queued)'}\n")

            # 2) wait for async processing (entity extraction is queued + LLM-bound)
            print("→ waiting for extraction to finish (polling up to 120s) ...")
            processed = False
            for i in range(40):
                await asyncio.sleep(3)
                hits = 0
                if snodes:
                    rn = await session.call_tool(
                        snodes, {"query": "Ada Lovelace", "group_ids": [group_id], "max_nodes": 10}
                    )
                    hits = _text(rn).lower().count("lovelace") + _text(rn).lower().count("ada")
                if hits:
                    processed = True
                    break
                print(f"  …{(i + 1) * 3}s")
            print()

            # 3) final search — nodes + facts
            ok = False
            if snodes:
                rn = await session.call_tool(
                    snodes, {"query": "Who was Ada Lovelace?", "group_ids": [group_id], "max_nodes": 10}
                )
                txt = _text(rn)
                print("=== search_nodes('Who was Ada Lovelace?') ===")
                print(txt[:1200] or "(empty)")
                ok = ok or "lovelace" in txt.lower() or "babbage" in txt.lower()
            if sfacts:
                rf = await session.call_tool(
                    sfacts, {"query": "Ada Lovelace Babbage", "group_ids": [group_id], "max_facts": 10}
                )
                txt = _text(rf)
                print("\n=== search_facts('Ada Lovelace Babbage') ===")
                print(txt[:1200] or "(empty)")
                ok = ok or "babbage" in txt.lower() or "engine" in txt.lower()
            if getep:
                re_ = await session.call_tool(getep, {"group_id": group_id, "last_n": 5})
                print("\n=== get_episodes ===")
                print(_text(re_)[:400] or "(empty)")

            print("\n" + "=" * 60)
            if ok:
                print("✅ PASS — Graphiti extracted entities/facts and FalkorDB returned them.")
                print(f"   (LLM + embeddings + graph store all working.)")
            elif processed:
                print("⚠️  PARTIAL — search returned but no expected entities matched.")
                print("   The stack is up; check the OPENAI_API_KEY / model is valid.")
            else:
                print("⚠️  TIMED OUT waiting for extraction.")
                print("   Server is reachable but the episode wasn't processed in time.")
                print("   Usually means the LLM key/model is wrong, or a 429 rate limit")
                print("   (lower SEMAPHORE_LIMIT). Check the graphiti service logs.")
            print(f"   Test data is under group_id='{group_id}' — clear it with the")
            print(f"   clear_graph tool or just ignore it.")
            print("=" * 60)
            return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(64)
    try:
        sys.exit(asyncio.run(main(sys.argv[1])))
    except Exception as e:  # noqa: BLE001
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        print("  - Is the URL the graphiti public domain? (a /mcp/ suffix is added)")
        print("  - Is the service deployed and healthy? Try: curl https://<domain>/health")
        sys.exit(3)
