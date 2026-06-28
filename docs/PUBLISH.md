# Publishing the one-click template

This template is built entirely from **prebuilt public images** (`falkordb/falkordb` and
`zepai/knowledge-graph-mcp:standalone`), so — unlike a source-built template — it does **not**
need this GitHub repo as the deploy source. The repo is the canonical config, docs, and
local smoke-test; the marketplace template itself references the two images directly.

> Prereq: Railway CLI **≥ 5.x** (`railway --version`), logged in (`railway login`). The
> `railway templates` command family does not exist in 4.x.

## A. Build the project once, then templatize (recommended)

Image-based, multi-service templates are most reliable when you first stand up the exact
project, then generate a template from it. The two-step `templates` flow then publishes it.

### 1. Create the project + two services

```bash
railway init -n graphiti-falkordb           # new project
```

Add **falkordb** (official image):

- Service name: `falkordb`
- Source: Docker image `falkordb/falkordb:latest`
- Variables:
  - `FALKORDB_PASSWORD = ${{ secret(16) }}`
  - `REDIS_ARGS = --requirepass ${{ FALKORDB_PASSWORD }}`
  - `BROWSER = 1`
- Volume: mount at `/var/lib/falkordb/data`
- Networking: keep `6379` **private**; optionally expose `3000` (browser UI).

Add **graphiti** (prebuilt image):

- Service name: `graphiti`
- Source: Docker image `zepai/knowledge-graph-mcp:standalone`
- Variables:
  - `OPENAI_API_KEY =` *(leave empty → becomes a required deploy input)*
  - `FALKORDB_URI = redis://${{ falkordb.RAILWAY_PRIVATE_DOMAIN }}:6379`
  - `FALKORDB_PASSWORD = ${{ falkordb.FALKORDB_PASSWORD }}`   # reference the same secret
  - `FALKORDB_DATABASE = default_db`
  - `MODEL_NAME = gpt-4o-mini`
  - `GRAPHITI_GROUP_ID = main`
  - `SEMAPHORE_LIMIT = 10`
- Networking: generate a **public domain → port 8000** (this is the `/mcp/` endpoint).

Deploy and confirm cold-start health before templatizing:

```bash
curl https://<graphiti-domain>/health        # expect 200
```

### 2. Create the template (unpublished draft)

```bash
railway templates create --json > template-create.out.json
# capture the returned template id
```

### 3. Publish to the marketplace

```bash
railway templates publish <template-id> \
  --category "AI/ML" \
  --readme-file README.md
```

The command returns the public **deploy code** → `https://railway.com/deploy/<code>`.
Put that URL behind the README deploy button.

## B. Variable design notes (the parts that bite)

- **Shared password.** Generate `${{ secret(16) }}` **once** on `falkordb`, then have
  `graphiti` reference it as `${{ falkordb.FALKORDB_PASSWORD }}` — do **not** generate a
  second secret, or the two services won't agree and Graphiti can't auth to the DB.
- **Private cross-service URI.** `${{ falkordb.RAILWAY_PRIVATE_DOMAIN }}` resolves to the
  internal hostname; FalkorDB listens on `6379` there. Never use the public domain for the
  DB link.
- **Required input.** Leaving `OPENAI_API_KEY` with an empty value makes Railway prompt for
  it on the deploy form — that is the one field the user must fill. Everything else has a
  default, so it stays a near one-click deploy.
- **Title/description.** Title comes from the project name (rename the project to set it);
  description ≤ 75 chars. Suggested:
  - Title: `Graphiti + FalkorDB — Knowledge Graph Memory for AI Agents`
  - Desc: `Real-time temporal knowledge-graph MCP server on fast, low-RAM FalkorDB.`
- **Assets.** Add a marketplace icon + hero to `assets/` and reference them with
  **commit-pinned** raw GitHub URLs (a moving `main` URL can break the card).

## C. Marketplace metadata checklist

- [ ] Category: `AI/ML`
- [ ] Icon + hero image set (commit-pinned URLs)
- [ ] README renders (it follows the Railway "Deploy and Host…" schema)
- [ ] Cold-start verified (`/health` 200) **before** publish
- [ ] `OPENAI_API_KEY` is the only required deploy input
- [ ] FalkorDB `6379` private; `3000` only public if intended
- [ ] Referral code appended to deploy/cross-links if desired (e.g. `?referralCode=jk_FgY`)

## D. After publishing

- Replace the placeholder deploy URL in `README.md` with the real
  `https://railway.com/deploy/<code>`.
- Metrics (active projects / deploy success) aren't in the CLI/API — scrape the public
  `railway.com/deploy/<code>` page to track them.
