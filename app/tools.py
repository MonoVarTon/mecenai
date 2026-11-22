"""Tools the concierge may call. The model only *asks* for a tool; this code executes it."""
import json
from pathlib import Path

CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))

TOOLS = [
    {
        "name": "find_artworks",
        "description": "Find artworks by series name or artwork title (partial match). Returns facts, "
                       "description and page link, without prices.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "series name or artwork title"}},
            "required": ["query"],
        },
    },
    {
        "name": "list_artworks",
        "description": "List artworks in the catalogue (titles, series, sizes, availability, links), "
                       "optionally only available ones or one series.",
        "input_schema": {
            "type": "object",
            "properties": {
                "series": {"type": "string", "description": "optional series name"},
                "available_only": {"type": "boolean"},
            },
        },
    },
    {
        "name": "get_price_rule",
        "description": "Artist-approved price for one artwork, in US dollars, shipping included. Never invent prices.",
        "input_schema": {
            "type": "object",
            "properties": {"artwork_id": {"type": "string"}},
            "required": ["artwork_id"],
        },
    },
]

PRIVATE = ("price_rule", "price_framed_usd", "price_note")


def public(a: dict, short: bool = False) -> dict:
    keep = {k: v for k, v in a.items() if k not in PRIVATE}
    if short:
        keep.pop("description", None)
    return keep


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
    if rule.startswith("usd:"):
        return f"${int(rule.split(':', 1)[1]):,}"
    return "price on request"  # unknown rule: never guess


def run_tool(name: str, args: dict):
    if name == "find_artworks":
        q = str(args.get("query") or args.get("series") or "").strip().lower().rstrip("s")
        if not q:
            return []
        found = [a for a in CATALOG["artworks"] if q in a["series"].lower() or q in a["title"].lower()]
        # prices are never exposed here: only get_price_rule returns approved wording
        return [public(a) for a in found]
    if name == "list_artworks":
        series = str(args.get("series") or "").strip().lower()
        in_series = [a for a in CATALOG["artworks"] if not series or series in a["series"].lower()]
        items = [a for a in in_series if not args.get("available_only") or a["available"]]
        return {"total_in_selection": len(in_series),
                "available": sum(a["available"] for a in in_series),
                "sold": sum(not a["available"] for a in in_series),
                "artworks": [public(a, short=True) for a in items]}
    if name == "get_price_rule":
        art = next((a for a in CATALOG["artworks"] if a["id"] == args["artwork_id"]), None)
        if art is None:
            return {"error": "unknown artwork"}
        out = {"artwork_id": art["id"], "title": art["title"], "price": describe_price(art["price_rule"]),
               "currency": "USD", "note": art.get("price_note") or CATALOG.get("price_policy", "")}
        if art.get("price_framed_usd") and art["available"]:
            out["price_framed"] = f"${art['price_framed_usd']:,}"
        return out
    return {"error": f"unknown tool {name}"}
