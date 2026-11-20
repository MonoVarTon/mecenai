import re

from fastapi.testclient import TestClient

from app import concierge
from app.main import app

client = TestClient(app)


def ask(text: str) -> dict:
    r = client.post("/chat", json={"message": text})
    assert r.status_code == 200
    return r.json()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_price_on_request_is_not_invented():
    data = ask("What do you have from the Quiet Harbors series?")
    assert data["tool_calls"] == ["find_artworks", "get_price_rule"]
    assert "price on request" in data["reply"]
    assert not re.search(r"[$€£]\s?\d", data["reply"]), "a number price appeared"


def test_price_follows_artist_rule():
    data = ask("Tell me about Glass Planets")
    assert "from $4,000" in data["reply"]


def test_unknown_series_hands_off_without_price():
    data = ask("Do you have anything with horses?")
    assert data["tool_calls"] == []
    assert "check with the artist" in data["reply"]
    assert not re.search(r"\d", data["reply"])


def test_empty_message_is_rejected():
    assert client.post("/chat", json={"message": ""}).status_code == 422


def test_loop_stops_after_max_steps():
    class StuckModel:
        def create(self, **_):
            return {"stop_reason": "tool_use",
                    "content": [{"type": "tool_use", "id": "t", "name": "find_artworks",
                                 "input": {"query": "Quiet Harbors"}}]}

    data = concierge.answer(StuckModel(), "hi")
    assert len(data["tool_calls"]) == concierge.MAX_STEPS
    assert "check with the artist" in data["reply"]


def test_find_artworks_hides_prices_and_matches_titles():
    from app.tools import run_tool
    found = run_tool("find_artworks", {"query": "Quiet Harbor I"})
    assert [a["id"] for a in found] == ["A1", "A2"] or found[0]["id"] == "A1"
    assert all("price_rule" not in a for a in found)
