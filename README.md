# Graphiti + FalkorDB — Knowledge-Graph Memory for AI Agents

> One-click Railway template: the **Graphiti MCP server** backed by **FalkorDB**, the
> official low-latency graph database. Give any MCP-capable agent (Claude, Cursor,
> Windsurf, your own app) a real-time, temporally-aware knowledge graph it can write to
> and query over HTTP. **Bring only an `OPENAI_API_KEY`.**

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/graphiti-falkordb)

<!-- Replace the deploy URL above with the published template code once `railway templates publish` returns it. See docs/PUBLISH.md. -->

![Graphiti temporal knowledge-graph walkthrough](assets/hero.gif)

---

## Deploy and Host Graphiti + FalkorDB on Railway

[Graphiti](https://github.com/getzep/graphiti) (by **Zep**) builds **real-time,
temporally-aware knowledge graphs** for AI agents — it extracts entities, relationships,
and *when each fact was true* from the text you feed it, so your agent gets memory that
updates incrementally instead of being re-indexed from scratch. This template runs
Graphiti's **MCP server** so any Model Context Protocol client can add episodes and search
the graph over plain HTTP.

Under the hood it stores the graph in [**FalkorDB**](https://www.falkordb.com/) — an
ultra-fast, Redis-based graph database (the official `falkordb/falkordb` container) that is
dramatically lighter on RAM than Neo4j, which keeps your Railway bill low.

## About Hosting Graphiti + FalkorDB

The template provisions **two linked services**:

| Service | Image | Role |
|---|---|---|
| **FalkorDB** | `falkordb/falkordb:latest` (official) | Persistent graph store + optional web browser UI. Talks to Graphiti over Railway's private network on `:6379`. Data lives on a volume at `/var/lib/falkordb/data`. |
| **Graphiti MCP** | `zepai/knowledge-graph-mcp:standalone` | The Graphiti knowledge-graph engine, exposed as an MCP HTTP endpoint on `:8000/mcp/`. Connects to FalkorDB via `FALKORDB_URI`. |

Railway handles networking, TLS, the public domain, logs, and restarts. The FalkorDB
password is **auto-generated** as a sealed secret and shared to both services, so the graph
store is never left open. You only set your LLM key.

## Why Deploy Graphiti + FalkorDB on Railway?

- **Lower RAM, lower bill** — FalkorDB is a Redis-core graph engine; it idles far below a
  comparable Neo4j deployment, and Railway bills by GB-hour of memory.
- **Real-time, time-aware memory** — Graphiti adds facts incrementally and tracks their
  validity over time, instead of recomputing the whole graph (the typical GraphRAG cost).
- **MCP-native** — point Claude Desktop, Cursor, Windsurf, or any MCP client at the public
  `/mcp/` URL and your agent can `add_episode` / `search` against a live knowledge graph.
- **Your keys, your data** — nothing is bundled; the graph persists on your own volume.
- **Two clean services** — scale, inspect, or back up the database independently of the app.

## Common Use Cases

- **Long-term agent memory** that stays current as facts change (people, projects, prefs).
- **A shared knowledge graph** several agents/apps read and write over MCP.
- **GraphRAG / entity-extraction pipelines** that need temporal context, not just vectors.

## Dependencies for Graphiti + FalkorDB Hosting

- An **OpenAI API key** (`OPENAI_API_KEY`) for entity extraction + embeddings. Other
  providers (Anthropic, Gemini, Azure, Groq) are supported via Graphiti config — see
  [docs/USAGE.md](docs/USAGE.md).

### Deployment Dependencies

- [Graphiti](https://github.com/getzep/graphiti) — open source, by Zep (MCP server image
  `zepai/knowledge-graph-mcp`).
- [FalkorDB](https://github.com/FalkorDB/FalkorDB) — open source graph database (official
  `falkordb/falkordb` container).

---

## Repo layout

```
.
├── docker-compose.yml   # canonical 2-service config — run it locally to verify before publish
├── .env.example         # the variables the template exposes
├── docs/
│   ├── ARCHITECTURE.md  # how the two services wire together on Railway
│   ├── USAGE.md         # connect an MCP client; swap LLM provider; tuning
│   └── PUBLISH.md       # exact `railway templates` steps + var wiring to ship the button
└── assets/              # marketplace icon + hero (add before publishing)
```

## Try it locally first

```bash
cp .env.example .env        # set OPENAI_API_KEY (+ pick a FALKORDB_PASSWORD)
docker compose up
# MCP endpoint:  http://localhost:8000/mcp/
# FalkorDB UI:   http://localhost:3000
# Health:        http://localhost:8000/health
```

See **[docs/PUBLISH.md](docs/PUBLISH.md)** to turn this into the one-click marketplace button.

## License

MIT — see [LICENSE](LICENSE). Graphiti and FalkorDB are the trademarks/property of their
respective owners; this template only orchestrates their official images.

The icon (`assets/icon.png`) and hero (`assets/hero.gif`) are the Graphiti/Zep brand mark
and demo animation from [getzep/graphiti](https://github.com/getzep/graphiti) (MIT),
included here for the marketplace listing of their software.
