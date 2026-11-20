"""The real-model adapter, tested against a fake HTTP endpoint (no network, no key)."""
import json

import httpx

from app import concierge
from app.models import OpenAICompatibleModel


def fake_provider(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content)
    assert body["tools"][0]["type"] == "function"
    if body["messages"][-1]["role"] == "user":
        msg = {"role": "assistant", "content": None, "tool_calls": [{
            "id": "call_1", "type": "function",
            "function": {"name": "find_artworks", "arguments": json.dumps({"series": "Quiet Harbors"})}}]}
    else:
        assert body["messages"][-1]["role"] == "tool"
        msg = {"role": "assistant", "content": "Quiet Harbor I is available, price on request."}
    return httpx.Response(200, json={"choices": [{"message": msg}], "usage": {"total_tokens": 10}})


def test_adapter_runs_agent_loop():
    model = OpenAICompatibleModel("test-key", "qwen/qwen3.8-27b", "https://example.test/v1/chat/completions",
                                  transport=httpx.MockTransport(fake_provider))
    data = concierge.answer(model, "What do you have from the Quiet Harbors series?")
    assert data["tool_calls"] == ["find_artworks"]
    assert "price on request" in data["reply"]
