# Mecenai

**An AI sales concierge for artists and galleries.**
Mecenai answers collectors 24/7 in their own language, knows every artwork in the catalogue, books viewings and hands the conversation to a human at the right moment.

> *Mecenai* — from *mecenate*, a patron of the arts, + AI. It connects artists with the collectors who will support them.

**Status:** early development (November 2026). This README describes where the product is going; each section is marked with its current state.

## Why

An artist's or gallery's website is often a beautiful catalogue that cannot answer a question. Collectors write at night, in other languages, and wait days for a reply. Mecenai turns the website into a conversation that leads to a viewing and a sale — in the artist's own voice, under the artist's own rules.

## What it will do

| Capability | How | State |
|---|---|---|
| Knows every artwork: story, technique, size, series, intent | retrieval over the catalogue (RAG, vector search) | planned |
| Speaks in the artist's voice, in the visitor's language (English, Arabic, Russian, …) | LLM with artist-approved instructions | planned |
| Quotes prices **only** by rules the artist approved — never negotiates or invents | tool calls with hard rules + tests | planned |
| Understands who is asking (collector, curator, press) and guides to a viewing | agent with state | planned |
| Hands off to a human in Telegram / WhatsApp | webhooks, n8n | planned |
| Exposes the catalogue to other AI agents | MCP server | planned |
| Optional certificate of authenticity on TON | TON, IPFS | planned |
| Insights for the artist: what collectors ask about | analytics | planned |
| Measured quality: no invented prices or facts | automated evaluations, published in this README | planned |
| One engine, many clients — each with its own catalogue and voice | multi-tenant service, Docker, cloud | planned |

## Principles

1. **No invented facts or prices.** If the answer is not in the catalogue or the rules, Mecenai says it will check with the artist and hands off.
2. **Honest about being an AI** when asked.
3. **Collectors' data is minimal and private** — privacy policy (including GDPR) from day one.
4. **Every number in this README comes from a measurement.**

## Open and closed

The engine, the MCP server, tests and evaluation results are open. Clients' catalogues, prices and conversations are never published; demos use a fictional artist.

## Built by

[Aliaksei](https://github.com/MonoVarTon) — architecture, backend, automation, TON — at **369 Aether**, a studio building websites for artists and galleries worldwide.
