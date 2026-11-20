"""An MCP client connects to the server in-process and uses it like Claude Desktop would."""
import json

import anyio
from mcp import Client

import mcp_server
from mcp_server import mcp


def run(coro_fn):
    return anyio.run(coro_fn)


def text(result) -> str:
    return result.content[0].text


def test_lists_tools_resources_prompts():
    async def go():
        async with Client(mcp) as c:
            tools = {t.name for t in (await c.list_tools()).tools}
            resources = {str(r.uri) for r in (await c.list_resources()).resources}
            prompts = {p.name for p in (await c.list_prompts()).prompts}
            return tools, resources, prompts

    tools, resources, prompts = run(go)
    assert tools == {"find_artworks", "get_price_rule", "request_viewing"}
    assert "catalog://artist" in resources
    assert "recommend_artwork" in prompts


def test_prices_only_via_rule():
    async def go():
        async with Client(mcp) as c:
            found = await c.call_tool("find_artworks", {"query": "Glass Planets"})
            price = await c.call_tool("get_price_rule", {"artwork_id": "A3"})
            cat = await c.read_resource("catalog://artist")
            return text(found), text(price), cat.contents[0].text

    found, price, cat = run(go)
    assert "Blue Orbit" in found and "price_rule" not in found
    assert "from $4,000" in price
    assert "price_rule" not in cat and "4000" not in cat


def test_request_viewing_validates(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_server, "REQUESTS_FILE", tmp_path / "req.jsonl")

    async def go():
        async with Client(mcp) as c:
            sold = await c.call_tool("request_viewing", {"artwork_id": "A2", "name": "Ann", "email": "ann@example.com"})
            bad = await c.call_tool("request_viewing", {"artwork_id": "A1", "name": "Ann", "email": "nope"})
            ok = await c.call_tool("request_viewing", {"artwork_id": "A1", "name": "Ann", "email": "ann@example.com"})
            return text(sold), text(bad), text(ok)

    sold, bad, ok = run(go)
    assert "not available" in sold
    assert "invalid email" in bad
    assert json.loads(ok)["ok"] is True
    assert (tmp_path / "req.jsonl").read_text().count("\n") == 1
