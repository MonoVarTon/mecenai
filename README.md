# Mecenai

**An AI sales concierge for artists and galleries.**
Mecenai answers collectors 24/7 in their own language, knows every artwork in the catalogue, books viewings and hands the conversation to a human at the right moment.

> *Mecenai* — from *mecenate*, a patron of the arts, + AI. It connects artists with the collectors who will support them.

**Status:** v0.3 (November 2026) — concierge on a real LLM (Groq), model evaluation, and an MCP server for other AI agents. This README describes where the product is going; each capability is marked with its current state.

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

Claude Desktop (`claude_desktop_config.json`):

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
| v0.4 | retrieval over artwork stories (RAG) |
| v0.5 | collector profiles and hand-off to Telegram |

## Principles

1. **No invented facts or prices.** If the answer is not in the catalogue or the rules, Mecenai says it will check with the artist and hands off.
2. **Honest about being an AI** when asked.
3. **Collectors' data is minimal and private** — privacy policy (including GDPR) from day one.
4. **Every number in this README comes from a measurement.**

## Open and closed

The engine, the MCP server, tests and evaluation results are open. Clients' catalogues, prices and conversations are never published; demos use a fictional artist.

## Built by

[Aliaksei](https://github.com/MonoVarTon) — architecture, backend, automation, TON — at **369 Aether**, a studio building websites for artists and galleries worldwide.
