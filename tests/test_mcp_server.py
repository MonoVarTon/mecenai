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
    assert tools == {"find_artworks", "list_artworks", "get_price_rule", "request_viewing"}
    assert "catalog://artist" in resources
    assert "recommend_artwork" in prompts


def test_prices_only_via_rule():
    async def go():
        async with Client(mcp) as c:
            found = await c.call_tool("find_artworks", {"query": "Venus"})
            price = await c.call_tool("get_price_rule", {"artwork_id": "venus"})
            cat = await c.read_resource("catalog://artist")
            return text(found), text(price), cat.contents[0].text

    found, price, cat = run(go)
    assert "Venus" in found and "price_rule" not in found and "1050" not in found
    assert "$1,050" in price
    assert "price_rule" not in cat and "1050" not in cat


def test_request_viewing_validates(tmp_path, monkeypatch):
    import app.tools as tools
    monkeypatch.setattr(tools, "REQUESTS_FILE", tmp_path / "req.jsonl")
    monkeypatch.setattr(tools, "CONTACT_URL", "")

    async def go():
        async with Client(mcp) as c:
            sold = await c.call_tool("request_viewing", {"artwork_id": "luna", "name": "Ann", "email": "ann@example.com"})
            bad = await c.call_tool("request_viewing", {"artwork_id": "venus", "name": "Ann", "email": "nope"})
            ok = await c.call_tool("request_viewing", {"artwork_id": "venus", "name": "Ann", "email": "ann@example.com"})
            return text(sold), text(bad), text(ok)

    sold, bad, ok = run(go)
    assert "not available" in sold
    assert "valid email" in bad
    assert json.loads(ok)["ok"] is True
    assert (tmp_path / "req.jsonl").read_text().count("\n") == 1
