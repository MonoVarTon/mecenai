"""Mecenai MCP server: the artist's catalogue for any AI assistant or agent.

Tools reuse app/tools.py, so the concierge and MCP clients follow the same price rules.
Run (stdio, e.g. for Claude Desktop):  python mcp_server.py
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from app.tools import CATALOG, public, run_tool

REQUESTS_FILE = Path(__file__).parent / "data" / "viewing_requests.jsonl"

mcp = MCPServer(
    name="mecenai",
    version="0.3.0",
    instructions=(
        "Catalogue of the painter Katsiaryna Budzko (budzko.art). Prices are available only through get_price_rule "
        "and must be quoted with the exact wording it returns. Never negotiate."
    ),
)


@mcp.tool()
def find_artworks(query: str) -> list[dict]:
    """Find artworks by series name or artwork title (partial match). Facts only, no prices."""
    return run_tool("find_artworks", {"query": query})


@mcp.tool()
def list_artworks(series: str = "", available_only: bool = False) -> list[dict]:
    """List artworks (titles, series, sizes, availability, links), optionally only available or one series."""
    return run_tool("list_artworks", {"series": series, "available_only": available_only})


@mcp.tool()
def get_price_rule(artwork_id: str) -> dict:
    """Artist-approved price for one artwork in US dollars, shipping included (e.g. '$1,050', 'sold')."""
    return run_tool("get_price_rule", {"artwork_id": artwork_id})


@mcp.tool()
def request_viewing(artwork_id: str, name: str, email: str, message: str = "") -> dict:
    """Ask the artist for a viewing of an available artwork. The artist confirms personally."""
    art = next((a for a in CATALOG["artworks"] if a["id"] == artwork_id), None)
    if art is None:
        return {"ok": False, "error": "unknown artwork"}
    if not art["available"]:
        return {"ok": False, "error": "this artwork is not available"}
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return {"ok": False, "error": "invalid email"}
    REQUESTS_FILE.parent.mkdir(exist_ok=True)
    record = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "artwork_id": artwork_id,
              "name": name[:100], "email": email[:200], "message": message[:1000]}
    with REQUESTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"ok": True, "status": "sent to the artist, who will reply personally"}


@mcp.resource("catalog://artist")
def catalog() -> str:
    """The whole catalogue without prices."""
    works = [public(a) for a in CATALOG["artworks"]]
    return json.dumps({"artist": CATALOG["artist"], "about": CATALOG.get("about", ""),
                       "website": CATALOG.get("website", ""), "artworks": works}, ensure_ascii=False, indent=2)


@mcp.prompt()
def recommend_artwork(wishes: str) -> str:
    """Pick artworks for a collector's wishes (room, colours, size, budget)."""
    return (f"A collector wants: {wishes}\n"
            "Use find_artworks and the catalog://artist resource to suggest up to 3 available works. "
            "For each, call get_price_rule and quote its wording exactly. Do not invent anything.")


if __name__ == "__main__":
    mcp.run()
