"""Tools the concierge may call. The model only *asks* for a tool; this code executes it."""
import json
from pathlib import Path

CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))

TOOLS = [
    {
        "name": "find_artworks",
        "description": "Find artworks in the catalogue by series name.",
        "input_schema": {
            "type": "object",
            "properties": {"series": {"type": "string"}},
            "required": ["series"],
        },
    },
    {
        "name": "get_price_rule",
        "description": "Return the artist-approved price rule for one artwork. Never invent prices.",
        "input_schema": {
            "type": "object",
            "properties": {"artwork_id": {"type": "string"}},
            "required": ["artwork_id"],
        },
    },
]


def series_names() -> list[str]:
    return sorted({a["series"] for a in CATALOG["artworks"]})


def describe_price(rule: str) -> str:
    """Turn a stored rule into the only wording the concierge is allowed to use."""
    if rule == "on_request":
        return "price on request"
    if rule == "sold":
        return "sold"
    if rule.startswith("from_usd:"):
        return f"from ${int(rule.split(':', 1)[1]):,}"
    return "price on request"  # unknown rule: never guess


def run_tool(name: str, args: dict):
    if name == "find_artworks":
        series = args["series"].strip().lower()
        return [a for a in CATALOG["artworks"] if a["series"].lower() == series]
    if name == "get_price_rule":
        art = next((a for a in CATALOG["artworks"] if a["id"] == args["artwork_id"]), None)
        if art is None:
            return {"error": "unknown artwork"}
        return {"artwork_id": art["id"], "price": describe_price(art["price_rule"])}
    return {"error": f"unknown tool {name}"}
