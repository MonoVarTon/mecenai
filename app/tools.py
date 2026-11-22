"""Tools the concierge may call. The model only *asks* for a tool; this code executes it."""
import json
import os
import re
import time
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

TOOLS.append({
    "name": "contact_artist",
    "description": "Send the visitor's request to the artist's email through the website contact form: purchase, "
                   "viewing, barter offer or custom request. Call ONLY after you showed the visitor the exact "
                   "message and they explicitly confirmed sending it.",
    "input_schema": {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["purchase", "viewing", "barter", "custom"]},
            "artwork_id": {"type": "string", "description": "optional"},
            "name": {"type": "string"},
            "email": {"type": "string", "description": "the visitor's email: the artist replies to it"},
            "other_contact": {"type": "string", "description": "optional Telegram or phone"},
            "details": {"type": "string", "description": "the confirmed message, in the visitor's words"},
        },
        "required": ["kind", "name", "email", "details"],
    },
})

REQUESTS_FILE = Path(__file__).resolve().parent.parent / "data" / "requests.jsonl"
CONTACT_URL = os.getenv("MECENAI_CONTACT_URL", "")          # e.g. https://budzko.art/api/contact
CONTACT_DAILY_CAP = int(os.getenv("MECENAI_CONTACT_PER_DAY", "20"))
CONTACT_PER_CLIENT = int(os.getenv("MECENAI_CONTACT_PER_CLIENT", "2"))
_sent = {"date": "", "count": 0, "per": {}}
SUBJECTS = {"purchase": "purchase", "viewing": "purchase", "barter": "general", "custom": "commission"}
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def send_to_artist(record: dict) -> bool:
    """Deliver through the artist's own website form (same inbox, reply goes straight to the visitor)."""
    if not CONTACT_URL:
        return False
    import httpx

    art = next((a for a in CATALOG["artworks"] if a["id"] == record["artwork_id"]), None)
    lines = [f"Request via Mecenai concierge ({record['kind']})"]
    if art:
        lines.append(f"Artwork: {art['title']} — {art['url']}")
    if record["other_contact"]:
        lines.append(f"Other contact: {record['other_contact']}")
    lines += ["", record["details"]]
    body = {"name": record["name"] or "Collector", "email": record["email"],
            "subject": SUBJECTS.get(record["kind"], "general"), "message": "\n".join(lines),
            "company": "", "elapsed": 10000}
    try:
        r = httpx.post(CONTACT_URL, json=body, timeout=15)
        return r.status_code == 200 and r.json().get("ok") is True
    except Exception:  # noqa: BLE001
        return False

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


def run_tool(name: str, args: dict, client: str = "anon"):
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
    if name == "contact_artist":
        email = str(args.get("email") or args.get("contact") or "").strip()
        email = email.translate({0x2011: "-", 0x2010: "-", 0x2013: "-", 0x00A0: None, 0x200B: None})
        if not EMAIL_RE.fullmatch(email):
            return {"ok": False, "error": "a valid email is required — the artist replies by email"}
        details = str(args.get("details") or "").strip()
        if not details:
            return {"ok": False, "error": "the message is empty"}
        today = time.strftime("%Y-%m-%d", time.gmtime())
        if _sent["date"] != today:
            _sent.update(date=today, count=0, per={})
        per = _sent.setdefault("per", {})
        if _sent["count"] >= CONTACT_DAILY_CAP or per.get(client, 0) >= CONTACT_PER_CLIENT:
            return {"ok": False, "error": "request limit reached — please write to the artist via the website form"}
        record = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                  "kind": str(args.get("kind", "custom"))[:20], "artwork_id": str(args.get("artwork_id") or "")[:60],
                  "name": str(args.get("name") or "")[:100], "email": email[:200],
                  "other_contact": str(args.get("other_contact") or "")[:200], "details": details[:3000]}
        REQUESTS_FILE.parent.mkdir(exist_ok=True)
        with REQUESTS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        if CONTACT_URL and not send_to_artist(record):
            return {"ok": False, "error": "sending failed — please use the contact form on the artist's website"}
        _sent["count"] += 1
        per[client] = per.get(client, 0) + 1
        return {"ok": True, "status": "sent to the artist by email; she will reply personally to the visitor's email"}
    return {"error": f"unknown tool {name}"}
