"""The agent loop: model asks for a tool -> our code runs it -> model continues -> final answer."""
import json

from .tools import TOOLS, run_tool

SYSTEM = (
    "You are Mecenai, a polite art concierge for the artist. Answer in the visitor's language, "
    "briefly, as a chat message (no tables). "
    "Use tools for every fact. Never invent prices: quote a price only as returned by "
    "get_price_rule — you may translate its wording into the visitor's language, never change numbers. "
    "All prices are in US dollars: always write them with $ (for example $4,000); never convert them "
    "to other currencies and never mention rubles, euros or exchange rates. "
    "If asked why a price is what it is, explain only with facts from the tools (size, technique, year, "
    "the price note) and offer to connect the visitor with the artist. "
    "Use the earlier messages of the conversation to understand follow-up questions. "
    "Prices already include worldwide shipping; special requests (framing, custom sizes, commissions) "
    "are discussed with the artist personally. When you mention a specific artwork, add its page link (url). "
    "Barter: only if the visitor proposes it (an exchange for goods, services or travel, partial barter as a "
    "discount, or a commission for the artist), say that the artist considers such offers personally for any work; "
    "ask what they offer, its approximate value in US dollars, location and timing, and a contact; then call "
    "contact_artist with kind 'barter'. Never accept, value or promise anything, and never suggest barter yourself. "
    "When a visitor wants to buy, view or discuss something special, offer to pass it to the artist and use "
    "contact_artist once they give a contact. "
    "Keep answers short, warm and concrete, like a gallery assistant. Write plain text for a chat window: "
    "no Markdown (no **, no #, no tables, no angle brackets around links); use simple line breaks and dashes for lists. Never invent descriptions, themes or stories that the tools did "
    "not return. Never accept, negotiate or confirm a deal: offer to pass the offer to the artist. "
    "If you are not sure, offer to check with the artist."
)

MAX_STEPS = 5


LANGS = {"en": "English", "ru": "Russian", "ar": "Arabic"}


def answer(model, question: str, history: list[dict] | None = None, lang: str | None = None) -> dict:
    messages = [{"role": m["role"], "content": m["content"]} for m in (history or [])
                if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)][-10:]
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    messages.append({"role": "user", "content": question})
    tool_calls: list[str] = []

    for _ in range(MAX_STEPS):
        system = SYSTEM if lang not in LANGS else (
            SYSTEM + f" The visitor chose {LANGS[lang]}: answer only in {LANGS[lang]} for the whole conversation.")
        reply = model.create(system=system, tools=TOOLS, messages=messages)
        if reply["stop_reason"] != "tool_use":
            text = " ".join(b["text"] for b in reply["content"] if b["type"] == "text")
            return {"reply": text, "tool_calls": tool_calls}

        results = []
        for call in (b for b in reply["content"] if b["type"] == "tool_use"):
            tool_calls.append(call["name"])
            results.append({
                "type": "tool_result",
                "tool_use_id": call["id"],
                "content": json.dumps(run_tool(call["name"], call["input"]), ensure_ascii=False),
            })
        messages += [
            {"role": "assistant", "content": reply["content"]},
            {"role": "user", "content": results},
        ]

    return {"reply": "Let me check with the artist and come back to you.", "tool_calls": tool_calls}
