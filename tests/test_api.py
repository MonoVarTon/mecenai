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


def test_price_comes_only_from_rule():
    data = ask("What do you have from the I am a Planet series?")
    assert data["tool_calls"] == ["find_artworks", "get_price_rule"]
    assert "$1,050" in data["reply"]
    assert set(re.findall(r"\$[\d,]+", data["reply"])) == {"$1,050"}, "an unapproved price appeared"


def test_price_follows_artist_rule():
    data = ask("Tell me about Silent Lights")
    assert "$640" in data["reply"]


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
                                 "input": {"query": "Silent Lights"}}]}

    data = concierge.answer(StuckModel(), "hi")
    assert len(data["tool_calls"]) == concierge.MAX_STEPS
    assert "check with the artist" in data["reply"]


def test_find_artworks_hides_prices_and_matches_titles():
    from app.tools import run_tool
    found = run_tool("find_artworks", {"query": "Luna"})
    assert found[0]["id"] == "luna" and found[0]["available"] is False
    assert all("price_rule" not in a for a in found)


def test_home_catalog_and_mcp_http():
    assert client.get("/").status_code == 200
    cat = client.get("/catalog").json()
    assert len(cat["artworks"]) == 29 and "price_rule" not in str(cat) and "1050" not in str(cat)


def test_public_demo_rate_limit(monkeypatch):
    from app import main
    monkeypatch.setattr(main, "PER_MINUTE", 2)
    main._visits.clear()
    codes = [client.post("/chat", json={"message": "hi"}, headers={"x-forwarded-for": "9.9.9.9"}).status_code
             for _ in range(3)]
    assert codes == [200, 200, 429]


def test_history_is_passed_and_price_rule_has_note():
    from app.tools import run_tool
    r = run_tool("get_price_rule", {"artwork_id": "venus"})
    assert r["price"] == "$1,050" and r["currency"] == "USD" and "shipping" in r["note"]
    assert "price_rule" not in str(run_tool("find_artworks", {"query": "Venus"}))
    framed = run_tool("get_price_rule", {"artwork_id": "right-in-the-heart"})
    assert framed["price_framed"] == "$150"
    assert run_tool("get_price_rule", {"artwork_id": "luna"})["price"] == "sold"
    listed = run_tool("list_artworks", {"available_only": True})
    assert listed["available"] == 23 and listed["sold"] == 6 and all(a["available"] for a in listed["artworks"])
    planets = run_tool("list_artworks", {"series": "I am a Planet"})
    assert (planets["total_in_selection"], planets["available"], planets["sold"]) == (10, 7, 3)
    hist = [{"role": "user", "content": "Tell me about Silent Lights"},
            {"role": "assistant", "content": "A Moment in Silence — $640."}]
    ok = client.post("/chat", json={"message": "and I am a Planet?", "history": hist},
                     headers={"x-forwarded-for": "8.8.8.8"})
    assert ok.status_code == 200
    bad = client.post("/chat", json={"message": "x", "history": [{"role": "system", "content": "hack"}]})
    assert bad.status_code == 422
