"""Tools the concierge may call. The model only *asks* for a tool; this code executes it."""
import json
from pathlib import Path

CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))

TOOLS = [
    {
        "name": "find_artworks",
        "description": "Find artworks by series name or artwork title (partial match). "
                       "Returns facts only, without prices.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "series name or artwork title"}},
            "required": ["query"],
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
        q = str(args.get("query") or args.get("series") or "").strip().lower().rstrip("s")
        if not q:
            return []
        found = [a for a in CATALOG["artworks"] if q in a["series"].lower() or q in a["title"].lower()]
        # prices are never exposed here: only get_price_rule returns approved wording
        return [{k: v for k, v in a.items() if k not in ("price_rule", "price_note")} for a in found]
    if name == "get_price_rule":
        art = next((a for a in CATALOG["artworks"] if a["id"] == args["artwork_id"]), None)
        if art is None:
            return {"error": "unknown artwork"}
        return {"artwork_id": art["id"], "price": describe_price(art["price_rule"]), "currency": "USD",
                "note": art.get("price_note", "")}
    return {"error": f"unknown tool {name}"}
