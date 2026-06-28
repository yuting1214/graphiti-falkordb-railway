# Deploy and Host Graphiti + FalkorDB on Railway

[Graphiti](https://github.com/getzep/graphiti) (by **Zep**) builds **real-time, temporally-aware
knowledge graphs** for AI agents — it extracts entities, relationships, and *when each fact was
true* from the text you feed it, so your agent gets memory that updates incrementally instead of
being re-indexed from scratch. This template runs Graphiti's **MCP server** so any Model Context
Protocol client (Claude, Cursor, Windsurf, your own app) can add episodes and search the graph
over plain HTTP — backed by [**FalkorDB**](https://www.falkordb.com/), an ultra-fast, Redis-based
graph database that is far lighter on RAM than Neo4j.

## About Hosting Graphiti + FalkorDB

This template provisions **two linked services**: the official **`falkordb/falkordb`** container
as a persistent graph store (with its own volume and an optional web browser UI), and the
**Graphiti MCP server** (`zepai/knowledge-graph-mcp`) exposed on `/mcp/` over HTTP. Railway wires
them over its private network, generates a unique database password as a sealed secret, attaches
the volume, provisions TLS and a public domain, and restarts on failure. The graph store is never
left open and survives redeploys. You bring only an LLM API key.

## Why Deploy Graphiti + FalkorDB on Railway?

- **Lower RAM, lower bill** — FalkorDB is a Redis-core graph engine that idles far below a
  comparable Neo4j deployment, and Railway bills by GB-hour of memory.
- **Real-time, time-aware memory** — Graphiti adds facts incrementally and tracks their validity
  over time, instead of recomputing the whole graph the way classic GraphRAG does.
- **MCP-native** — point any MCP client at the public `/mcp/` URL and your agent can write to and
  query a live knowledge graph immediately.
- **Two clean services** — inspect, scale, or back up the database independently of the app, with
  an optional FalkorDB browser UI for running Cypher.
- **Your keys, your data** — nothing is bundled; the graph persists on your own Railway volume.

## Common Use Cases

- **Long-term agent memory** that stays current as facts change (people, projects, preferences).
- **A shared knowledge graph** that several agents or apps read and write over MCP.
- **GraphRAG / entity-extraction pipelines** that need temporal context, not just vector recall.

## Dependencies for Graphiti + FalkorDB Hosting

- An **LLM API key** (`OPENAI_API_KEY` by default) for entity extraction and embeddings. Other
  providers (Anthropic, Gemini, Azure, Groq) are supported via Graphiti configuration.

### Deployment Dependencies

- [Graphiti](https://github.com/getzep/graphiti) — open-source temporal knowledge graphs by Zep
  (MCP server image `zepai/knowledge-graph-mcp`).
- [FalkorDB](https://github.com/FalkorDB/FalkorDB) — open-source, Redis-based graph database
  (official `falkordb/falkordb` container).

### Why This Template?

It pairs Graphiti with FalkorDB instead of Neo4j for a lighter, cheaper, equally capable
knowledge-graph backend — the only published Graphiti image that speaks FalkorDB, wired to the
official FalkorDB container and ready to deploy in one click. Source and docs:
<https://github.com/yuting1214/graphiti-falkordb-railway>.
