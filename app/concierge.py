"""The agent loop: model asks for a tool -> our code runs it -> model continues -> final answer."""
import hashlib
import hmac
import json
import os
import re
import secrets

from .tools import CATALOG, TOOLS, run_tool

SYSTEM = (
    "You are Mecenai, a polite art concierge for the artist Katsiaryna Budzko (a woman; in Russian say "
    "'художница', her name is 'Катерина Будзько'). Answer in the visitor's language, "
    "briefly, as a chat message (no tables). "
    "Use tools for every fact. Never invent prices: quote a price only as returned by "
    "get_price_rule — you may translate its wording into the visitor's language, never change numbers. "
    "All prices are in US dollars: always write them with $ (for example $4,000); never convert them "
    "to other currencies and never mention rubles, euros or exchange rates. "
    "If asked why a price is what it is, explain only with facts from the tools (size, technique, year, "
    "the price note) and offer to connect the visitor with the artist. "
    "Use the earlier messages of the conversation to understand follow-up questions. "
    "Prices already include worldwide shipping; special requests (framing, custom sizes, commissions) "
    "are discussed with the artist personally. When you mention a specific artwork, add its page link (url). "
    "Barter: only if the visitor proposes it (an exchange for goods, services or travel, partial barter as a "
    "discount, or a commission for the artist), say that the artist considers such offers personally for any work; "
    "ask what they offer, its approximate value in US dollars, location and timing; then prepare the request "
    "the same way (name, email, confirmation) with kind 'barter'. Never accept, value or promise anything, and never suggest barter yourself. "
    "When a visitor wants to buy, view or discuss something special, offer to send their request to the artist "
    "by email. Ask for their name and email (required — the artist replies by email), optionally Telegram or phone. "
    "Then show the exact message you will send to the artist (name, email, artwork, text), explain that the artist "
    "will reply to the visitor's email, and ask 'Send it?'. Copy email addresses exactly as typed. Call contact_artist "
    "ONLY after the visitor clearly confirms; never send without confirmation. "
    "Keep answers short, warm and concrete, like a gallery assistant. Write plain text for a chat window: "
    "no Markdown (no **, no #, no tables, no angle brackets around links); use simple line breaks and dashes for lists. Never invent descriptions, themes or stories that the tools did "
    "not return. Never accept, negotiate or confirm a deal: offer to pass the offer to the artist. "
    "If you are not sure, offer to check with the artist."
)

MAX_STEPS = 5

# "ghbdtn" -> "привет": a Russian visitor typing with the English keyboard layout.
_EN = "qwertyuiop[]asdfghjkl;'zxcvbnm,.`QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>~"
_RU = "йцукенгшщзхъфывапролджэячсмитьбюёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЁ"
_LAYOUT = str.maketrans(_EN, _RU)


def fix_layout(text: str) -> str:
    """Return the Russian reading of text typed in the wrong layout, or the text unchanged."""
    if re.search(r"[а-яА-ЯёЁ]", text) or re.search(r"https?://|@", text):
        return text
    letters = [c for c in text.lower() if "a" <= c <= "z"]
    if len(letters) < 4:
        return text
    en_vowels = sum(c in "aeiouy" for c in letters) / len(letters)
    ru = text.translate(_LAYOUT)
    ru_letters = [c for c in ru.lower() if "а" <= c <= "я" or c == "ё"]
    ru_vowels = sum(c in "аеёиоуыэюя" for c in ru_letters) / max(len(ru_letters), 1)
    return ru if en_vowels < 0.22 and ru_vowels > 0.3 else text



LANGS = {"en": "English", "ru": "Russian", "ar": "Arabic"}

# Assistant turns in the history come back from the browser, so they are signed (HMAC, as in lesson 1):
# a visitor cannot forge "the assistant already confirmed…" or invent earlier prices.
_SECRET = (os.getenv("MECENAI_HISTORY_SECRET") or secrets.token_hex(32)).encode()


def sign(text: str) -> str:
    return hmac.new(_SECRET, text.encode(), hashlib.sha256).hexdigest()


def _clean_history(history: list[dict] | None) -> list[dict]:
    out = []
    for m in history or []:
        role, content = m.get("role"), m.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            continue
        if role == "assistant" and not hmac.compare_digest(str(m.get("sig") or ""), sign(content)):
            continue  # forged or tampered assistant turn
        out.append({"role": role, "content": content})
    return out[-10:]


_MONEY = re.compile(r"\$\s?(\d[\d,\s\u00a0\u202f]*)|(\d[\d,\s\u00a0\u202f]*)\s?(?:\$|USD|долл)")


def _amounts(text: str) -> set[int]:
    found = set()
    for m in _MONEY.finditer(text):
        digits = re.sub(r"\D", "", m.group(1) or m.group(2) or "")
        if digits:
            found.add(int(digits))
    return found


FALLBACK_REPLY = {
    "ru": "Уточню это у художницы и вернусь с ответом — могу передать ей ваш вопрос.",
    "ar": "سأتحقق من ذلك مع الفنانة — يمكنني إرسال سؤالك إليها.",
    "en": "Let me check with the artist and come back to you — I can pass your question to her.",
}

SAFE_PRICE_REPLY = {
    "ru": "Уточню точную цену у художницы — могу передать ей ваш вопрос.",
    "ar": "سأتحقق من السعر الدقيق مع الفنانة — يمكنني إرسال سؤالك إليها.",
    "en": "Let me confirm the exact price with the artist — I can pass your question to her.",
}


def plain(text: str) -> str:
    """The chat window shows plain text: strip Markdown the model sometimes adds anyway."""
    text = re.sub(r"\*\*|__", "", text)
    text = re.sub(r"(?<![\w*])\*(?=\S)([^*\n]+?)(?<=\S)\*(?![\w*])", r"\1", text)
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)
    # "$I Hear$" (formula-style quoting) -> «I Hear»; real prices like "$95" are never touched
    text = re.sub(r"\$([^\W\d_][^$\n]{0,80}?)\$", r"«\1»", text)
    return re.sub(r"<(https?://[^>\s]+)>", r"\1", text)


def answer(model, question: str, history: list[dict] | None = None, lang: str | None = None,
           client: str = "anon", artwork_id: str | None = None) -> dict:
    messages = _clean_history(history)
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    fixed = fix_layout(question)
    if fixed != question:
        lang = "ru"  # the browser guessed English from Latin letters, but the visitor writes Russian
    messages.append({"role": "user", "content": fixed})
    tool_calls: list[str] = []

    for step in range(MAX_STEPS):
        last = step == MAX_STEPS - 1
        system = SYSTEM if lang not in LANGS else (
            SYSTEM + f" The visitor chose {LANGS[lang]}: answer only in {LANGS[lang]} for the whole conversation.")
        art = next((a for a in CATALOG["artworks"] if a["id"] == artwork_id), None) if artwork_id else None
        if art:
            system += (f" The visitor is now on the page of the artwork '{art['title']}' (id {art['id']}); "
                       "'this painting' means this artwork.")
        if last:  # out of tool budget: answer from what is already known
            system += " Do not call tools any more: answer now from the tool results above."
        reply = model.create(system=system, tools=[] if last else TOOLS, messages=messages)
        if reply["stop_reason"] == "tool_use" and last:
            break
        if reply["stop_reason"] != "tool_use":
            text = plain(" ".join(b["text"] for b in reply["content"] if b["type"] == "text"))
            # Output guard: every dollar amount must come from a tool result or the conversation itself.
            allowed = set()
            for m in messages:
                c = m["content"]
                allowed |= _amounts(c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))
            if _amounts(text) - allowed:
                text = SAFE_PRICE_REPLY.get(lang or "en", SAFE_PRICE_REPLY["en"])
            return {"reply": text, "tool_calls": tool_calls, "sig": sign(text)}

        results = []
        for call in (b for b in reply["content"] if b["type"] == "tool_use"):
            tool_calls.append(call["name"])
            results.append({
                "type": "tool_result",
                "tool_use_id": call["id"],
                "content": json.dumps(run_tool(call["name"], call["input"], client), ensure_ascii=False),
            })
        messages += [
            {"role": "assistant", "content": reply["content"]},
            {"role": "user", "content": results},
        ]

    text = FALLBACK_REPLY.get(lang or "en", FALLBACK_REPLY["en"])
    return {"reply": text, "tool_calls": tool_calls, "sig": sign(text)}
