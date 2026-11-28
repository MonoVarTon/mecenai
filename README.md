# Mecenai

**An AI sales concierge for artists and galleries.**
Mecenai answers collectors 24/7 in their own language, knows every artwork in the catalogue, books viewings and hands the conversation to a human at the right moment.

> *Mecenai* — from *mecenate*, a patron of the arts, + AI. It connects artists with the collectors who will support them.

**▶ Live demo: [mecenai.onrender.com](https://mecenai.onrender.com)** · MCP endpoint: `https://mecenai.onrender.com/mcp/` (the free instance sleeps when idle — the first request may take up to a minute)

**▶ In production: [budzko.art](https://budzko.art)** — the concierge of painter Katsiaryna Budzko, on every page of her site (button *Ask about a painting*).

**Status:** v0.4 (November 2026) — concierge on a real LLM (Groq), model evaluation, an MCP server for other AI agents, and a public demo. This README describes where the product is going; each capability is marked with its current state.

## Why

An artist's or gallery's website is often a beautiful catalogue that cannot answer a question. Collectors write at night, in other languages, and wait days for a reply. Mecenai turns the website into a conversation that leads to a viewing and a sale — in the artist's own voice, under the artist's own rules.

## What it will do

| Capability | How | State |
|---|---|---|
| Knows every artwork: story, technique, size, series, intent | retrieval over the catalogue (RAG, vector search) | planned |
| Speaks in the artist's voice, in the visitor's language (English, Arabic, Russian, …) | LLM with artist-approved instructions | **v0.2** — gpt-oss-120b via Groq |
| Quotes prices **only** by rules the artist approved — never negotiates or invents | tool calls with hard rules + tests | **v0.1** — scripted model |
| Understands who is asking (collector, curator, press) and guides to a viewing | agent with state | planned |
| Hands off to a human in Telegram / WhatsApp | webhooks, n8n | planned |
| Exposes the catalogue to other AI agents | MCP server | **v0.3** — tools, resource, prompt |
| Optional certificate of authenticity on TON | TON, IPFS | planned |
| Insights for the artist: what collectors ask about | analytics | planned |
| Measured quality: no invented prices or facts | automated evaluations | **started** — [model comparison](docs/evals/2026-11-20-model-comparison.md) |
| One engine, many clients — each with its own catalogue and voice | multi-tenant service, Docker, cloud | planned |

## Run it (v0.1)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```bash
curl localhost:8000/health
curl -X POST localhost:8000/chat -H "content-type: application/json" \
     -d '{"message": "What do you have from the Quiet Harbors series?"}'
```

v0.1 runs offline on a scripted model that speaks the Messages API format, so it needs no API key. The catalogue belongs to a fictional artist.

```
app/
  main.py        FastAPI: GET /health, POST /chat
  concierge.py   agent loop: model asks for a tool -> code runs it -> model continues
  tools.py       find_artworks, get_price_rule (artist-approved wording only)
  models.py      scripted model for tests + any OpenAI-compatible LLM (Groq)
  catalog.json   fictional demo catalogue
mcp_server.py    MCP server: tools, resource, prompt
scripts/         model comparison
docs/evals/      evaluation results
tests/           API, price rules, hand-off, model adapter, MCP server
```

### MCP server

Any MCP client (Claude Desktop, IDEs, other agents) can use the catalogue:

| Kind | Name | What |
|---|---|---|
| tool | `find_artworks` | search by series or title, facts only |
| tool | `get_price_rule` | the only way to get a price — artist-approved wording |
| tool | `request_viewing` | ask the artist for a viewing (validated, the artist replies personally) |
| resource | `catalog://artist` | the whole catalogue without prices |
| prompt | `recommend_artwork` | pick works for a collector's wishes |

Remote (any client that supports Streamable HTTP): `https://mecenai.onrender.com/mcp/`

Local, Claude Desktop (`claude_desktop_config.json`):

```json
{"mcpServers": {"mecenai": {"command": "python", "args": ["/path/to/mecenai/mcp_server.py"]}}}
```

Real model: copy `.env.example` to `.env`, set `MECENAI_MODEL=groq` and `GROQ_API_KEY`.

Tests: `pytest -q` — they also run on every push (GitHub Actions).

## Roadmap

| Version | What |
|---|---|
| v0.1 | service skeleton, tool calls, price rules, tests — **done** |
| v0.2 | real LLM backend behind the same interface; model comparison — **done** |
| v0.3 | MCP server: the catalogue for other AI agents — **done** |
| v0.4 | public demo and MCP over HTTP (Render), abuse limits — **done** |
| v0.5 | retrieval over artwork stories (RAG) |
| v0.6 | collector profiles and hand-off to Telegram |

## Principles

1. **No invented facts or prices.** If the answer is not in the catalogue or the rules, Mecenai says it will check with the artist and hands off.
2. **Honest about being an AI** when asked.
3. **Collectors' data is minimal and private** — privacy policy (including GDPR) from day one.
4. **Every number in this README comes from a measurement.**

## In production: budzko.art

Mecenai runs on **[budzko.art](https://budzko.art)**, the website and shop of figurative painter Katsiaryna Budzko (29 works, two series).

| What | How it is wired |
|---|---|
| Embed | one line on every page: `<script src="/mecenai-widget.js" defer></script>` — a copy of [`app/static/widget.js`](app/static/widget.js) |
| Isolation | the chat lives in an iframe from `mecenai.onrender.com`; the site's CSP allows it with a single `frame-src`, nothing else is loosened |
| Context | on a painting page (`/gallery/<id>/`) the widget passes the artwork id, so the concierge knows what the visitor is looking at |
| Catalogue | [`app/catalog.json`](app/catalog.json) mirrors the site's public catalogue: titles, sizes, availability, price rules |
| Hand-off | “contact the artist” requests go to the artist's inbox; the visitor can also buy directly through the site's checkout |
| Protection | `frame-ancestors` lets only budzko.art embed the chat; per-visitor limits on messages and e-mails |

The site itself lives in a separate private repository (`MonoVarTon/budzko-art`).

## Open and closed

The engine, the MCP server, tests and evaluation results are open. Conversations are never published. The bundled catalogue is the public catalogue of budzko.art, used with the artist's consent; other clients' catalogues stay private.

## Built by

[Alexey](https://github.com/MonoVarTon) — architecture, backend, automation, TON — at **[369 Aether](https://369aether.net/)**, a studio building websites for artists and galleries worldwide.
