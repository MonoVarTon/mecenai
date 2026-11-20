"""The agent loop: model asks for a tool -> our code runs it -> model continues -> final answer."""
import json

from .tools import TOOLS, run_tool

SYSTEM = (
    "You are Mecenai, a polite art concierge for the artist. Answer in the visitor's language, "
    "briefly, as a chat message (no tables). "
    "Use tools for every fact. Never invent prices: quote a price only with the exact wording "
    "returned by get_price_rule. Never invent descriptions, themes or stories that the tools did "
    "not return. Never accept, negotiate or confirm a deal: offer to pass the offer to the artist. "
    "If you are not sure, offer to check with the artist."
)

MAX_STEPS = 5


def answer(model, question: str) -> dict:
    messages = [{"role": "user", "content": question}]
    tool_calls: list[str] = []

    for _ in range(MAX_STEPS):
        reply = model.create(system=SYSTEM, tools=TOOLS, messages=messages)
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
