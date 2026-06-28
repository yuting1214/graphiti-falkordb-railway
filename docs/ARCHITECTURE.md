# Architecture

```
                         Internet
                            │  HTTPS (Railway public domain)
                            ▼
                ┌───────────────────────────┐
                │  graphiti  (service)       │
                │  zepai/knowledge-graph-mcp │
                │  :standalone               │
                │                            │
                │  MCP server  :8000 /mcp/   │  ◀── your agent / MCP client
                │  health      :8000 /health │
                └─────────────┬──────────────┘
                              │  redis://<falkordb>.railway.internal:16379
                              │  (Railway private network, auth = shared secret)
                              ▼
                ┌───────────────────────────┐
                │  falkordb  (service)       │
                │  falkordb/falkordb:latest  │
                │                            │
                │  graph proto :16379         │
                │  browser UI  :3000 (opt)   │
                │  volume  /var/lib/falkordb/data
                └───────────────────────────┘
```

## Why this shape

- **Graphiti needs the `:standalone` image.** The mainline `zepai/graphiti` REST server
  and the standard `zepai/knowledge-graph-mcp:latest` image only support **Neo4j** today
  (see getzep/graphiti issue #749). The `:standalone` build is the only published Graphiti
  image that speaks FalkorDB, so that is what the `graphiti` service runs. We point it at a
  **separate** FalkorDB via `FALKORDB_URI`; the persistent graph therefore lives on the
  `falkordb` service's volume, not inside the app container.
- **FalkorDB is the official `falkordb/falkordb` container** — same image the standalone
  `falkordb-1` Railway template uses — so you get the upstream graph engine plus its
  browser UI, independently restartable and backup-able.

## Service wiring (Railway)

| Variable | `falkordb` | `graphiti` | Value |
|---|:--:|:--:|---|
| `FALKORDB_PASSWORD` | ✅ | ✅ | `${{ secret(32, "A-Za-z") }}` — generated once (URL-safe), shared to both |
| `REDIS_ARGS` | ✅ | | `--requirepass ${{ FALKORDB_PASSWORD }}` |
| `FALKORDB_PORT` | ✅ | | `16379` (FalkorDB binds here, via `FALKORDB_ARGS`) |
| `FALKORDB_ARGS` | ✅ | | `--port ${{ FALKORDB_PORT }} --bind 0.0.0.0 :: --protected-mode no` |
| `BROWSER` | ✅ | | `1` (web UI on `:3000`) |
| `FALKORDB_URI` | | ✅ | `redis://${{ falkordb.RAILWAY_PRIVATE_DOMAIN }}:${{ falkordb.FALKORDB_PORT }}` |
| `FALKORDB_PASSWORD` | | ✅ | `${{ falkordb.FALKORDB_PASSWORD }}` (same secret) |
| `FALKORDB_DATABASE` | | ✅ | `default_db` |
| `OPENAI_API_KEY` | | ✅ | **user-provided (required)** |
| `MODEL_NAME` | | ✅ | `gpt-5.4-mini-2026-03-17` (optional) |
| `GRAPHITI_GROUP_ID` | | ✅ | `main` (optional) |
| `SEMAPHORE_LIMIT` | | ✅ | `10` (lower on rate-limited keys) |

- **Public domain → `graphiti` on port 8000.** That is the MCP endpoint clients hit.
- **FalkorDB stays private** (16379 over `railway.internal`); only expose `:3000` publicly if
  you actually want the browser UI reachable — it is password-protected by the same secret.
- Graphiti waits for FalkorDB to be reachable before serving; Railway's restart policy
  retries until the dependency is up.

## Footprint

FalkorDB is a Redis-core engine and idles in the tens of MB; the standalone Graphiti image
is ~125 MB on disk. The combination is meaningfully lighter on RAM (and therefore on
Railway's GB-hour billing) than an equivalent Neo4j-backed Graphiti stack.

> Note: the `:standalone` image bundles a FalkorDB binary for its single-container mode.
> In this two-service setup we override `FALKORDB_URI` to the external service, so any
> in-container FalkorDB is unused/ephemeral — the durable data is on the `falkordb`
> service's volume.
