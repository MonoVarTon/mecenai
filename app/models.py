"""Model backends. v0.1 ships a scripted mock that speaks the Messages API format,
so the service and its tests run offline, for free and deterministically."""
import json

from .tools import series_names


def _text(question: str) -> str:
    return question if isinstance(question, str) else ""


class ScriptedModel:
    """Deterministic stand-in for an LLM: decides on tool calls the way a real model would."""

    def create(self, system: str, tools: list, messages: list) -> dict:
        last = messages[-1]

        # 1) A fresh visitor question -> look for a series name, ask for find_artworks.
        if last["role"] == "user" and isinstance(last["content"], str):
            q = _text(last["content"]).lower()
            series = next((s for s in series_names() if s.lower() in q), None)
            if series is None:
                return self._end("I don't want to guess — let me check with the artist and come back to you.")
            return self._tool("find_artworks", {"series": series}, "Let me check the catalogue.")

        # 2) A tool result came back.
        result = json.loads(last["content"][0]["content"])
        if isinstance(result, list):  # result of find_artworks
            available = [a for a in result if a["available"]]
            if not available:
                return self._end(f"All {len(result)} works of this series are already sold. "
                                 "Shall I tell you about other series?")
            return self._tool("get_price_rule", {"artwork_id": available[0]["id"]})

        # 3) Price rule came back -> final answer, using only the approved wording.
        works = self._found(messages)
        art = next(a for a in works if a["id"] == result["artwork_id"])
        available = sum(1 for a in works if a["available"])
        return self._end(
            f"The series {art['series']} has {len(works)} work(s); {available} available: "
            f"«{art['title']}», {art['technique']}, {art['size_cm']} cm — {result['price']}. "
            "Shall I arrange a viewing or connect you with the artist?"
        )

    @staticmethod
    def _found(messages: list) -> list:
        for m in messages:
            if m["role"] == "user" and isinstance(m["content"], list):
                data = json.loads(m["content"][0]["content"])
                if isinstance(data, list):
                    return data
        return []

    @staticmethod
    def _tool(name: str, args: dict, text: str = "") -> dict:
        content = [{"type": "text", "text": text}] if text else []
        content.append({"type": "tool_use", "id": f"toolu_{name}", "name": name, "input": args})
        return {"stop_reason": "tool_use", "content": content}

    @staticmethod
    def _end(text: str) -> dict:
        return {"stop_reason": "end_turn", "content": [{"type": "text", "text": text}]}
