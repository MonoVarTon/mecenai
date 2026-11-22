"""Model backends. v0.1 ships a scripted mock that speaks the Messages API format,
so the service and its tests run offline, for free and deterministically."""
import json
import time

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
            return self._tool("find_artworks", {"query": series}, "Let me check the catalogue.")

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


class OpenAICompatibleModel:
    """Real LLM over any OpenAI-compatible endpoint (Groq by default).
    Translates our Messages-API-style conversation to chat/completions and back,
    so the agent loop does not depend on the provider."""

    def __init__(self, api_key: str, model: str, url: str, transport=None, timeout: float = 30.0):
        import httpx

        if not api_key:
            raise RuntimeError("API key is missing: set it in .env")
        self.model = model
        self.url = url
        self.client = httpx.Client(timeout=timeout, transport=transport,
                                   headers={"Authorization": f"Bearer {api_key}"})

    @staticmethod
    def to_openai(system: str, tools: list, messages: list) -> dict:
        out = [{"role": "system", "content": system}]
        for m in messages:
            if isinstance(m["content"], str):
                out.append({"role": m["role"], "content": m["content"]})
            elif m["role"] == "assistant":
                text = " ".join(b["text"] for b in m["content"] if b["type"] == "text") or None
                calls = [{"id": b["id"], "type": "function",
                          "function": {"name": b["name"], "arguments": json.dumps(b["input"])}}
                         for b in m["content"] if b["type"] == "tool_use"]
                out.append({"role": "assistant", "content": text, "tool_calls": calls})
            else:  # tool results
                for b in m["content"]:
                    out.append({"role": "tool", "tool_call_id": b["tool_use_id"], "content": b["content"]})
        return {
            "messages": out,
            "tools": [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                         "parameters": t["input_schema"]}} for t in tools],
        }

    @staticmethod
    def from_openai(data: dict) -> dict:
        msg = data["choices"][0]["message"]
        content = []
        if msg.get("content"):
            content.append({"type": "text", "text": msg["content"]})
        for c in msg.get("tool_calls") or []:
            content.append({"type": "tool_use", "id": c["id"], "name": c["function"]["name"],
                            "input": json.loads(c["function"]["arguments"] or "{}")})
        stop = "tool_use" if any(b["type"] == "tool_use" for b in content) else "end_turn"
        return {"stop_reason": stop, "content": content, "usage": data.get("usage", {})}

    def create(self, system: str, tools: list, messages: list) -> dict:
        body = {"model": self.model, "temperature": 0.2, **self.to_openai(system, tools, messages)}
        for attempt in range(4):  # retry + backoff on rate limits (429) and busy provider (5xx)
            r = self.client.post(self.url, json=body)
            if r.status_code not in (429, 500, 502, 503) or attempt == 3:
                break
            try:
                wait = float(r.headers.get("retry-after", ""))
            except ValueError:
                wait = 2.0 ** attempt
            time.sleep(min(max(wait, 0.5), 10.0))
        r.raise_for_status()
        return self.from_openai(r.json())


def build_model():
    from . import config

    if config.MODEL_BACKEND == "groq":
        return OpenAICompatibleModel(config.GROQ_API_KEY, config.GROQ_MODEL, config.GROQ_URL)
    return ScriptedModel()
