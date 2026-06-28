# Usage

## 1. Connect an MCP client

After deploy, Railway gives the **graphiti** service a public domain. The MCP endpoint is:

```
https://<your-graphiti-domain>/mcp/
```

### Claude Desktop / Cursor / Windsurf (HTTP MCP)

```jsonc
{
  "mcpServers": {
    "graphiti": {
      "transport": "http",
      "url": "https://<your-graphiti-domain>/mcp/"
    }
  }
}
```

Clients that only speak stdio can bridge with `npx mcp-remote https://<domain>/mcp/`.

### Core tools exposed by the Graphiti MCP server

- `add_episode` / `add_memory` — feed text (or JSON) so Graphiti extracts entities,
  relationships, and their valid-time into the graph.
- `search_nodes` / `search_facts` — hybrid semantic + graph search over what it has learned.
- `get_episodes`, `delete_episode`, `clear_graph` — manage stored memory.

Health check (for uptime monitors): `GET https://<your-graphiti-domain>/health`.

## 2. Inspect the graph (FalkorDB browser UI)

If you exposed the `falkordb` service's `:3000` port, open it in a browser and authenticate
with `FALKORDB_PASSWORD` to run Cypher against the live graph. Keep it private unless you
need it.

## 3. Swap the LLM provider

The standalone image defaults to OpenAI. To use another provider, set the matching env vars
on the **graphiti** service (Graphiti reads provider config from the environment):

| Provider | Key variables |
|---|---|
| OpenAI (default) | `OPENAI_API_KEY`, `MODEL_NAME`, `EMBEDDER_MODEL` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` |
| Anthropic | `ANTHROPIC_API_KEY`, `MODEL_NAME=claude-...` (embeddings still need an OpenAI/other key) |
| Google Gemini | `GOOGLE_API_KEY`, `MODEL_NAME=gemini-...` |
| Groq | `GROQ_API_KEY`, `MODEL_NAME=...` |

See the Graphiti MCP server README for the full provider matrix:
<https://github.com/getzep/graphiti/blob/main/mcp_server/README.md>

## 4. Tuning

- **LLM 429 / rate-limit errors** → lower `SEMAPHORE_LIMIT` (try `1`–`5` on free/low tiers).
- **Multiple isolated graphs** → give each client a distinct `GRAPHITI_GROUP_ID`.
- **Cost / model** → the default `gpt-5.4-mini-2026-03-17` + `text-embedding-3-small`
  is a fast, low-cost combo with strong tool-use; set `MODEL_NAME` to any OpenAI model
  id (or `gpt-5.4-mini` to auto-track the latest snapshot) for different cost/quality.

## 5. Backups

The graph is on the `falkordb` service's volume (`/var/lib/falkordb/data`). Snapshot it from
the Railway dashboard, or `railway ssh` into the service and copy the RDB file.
