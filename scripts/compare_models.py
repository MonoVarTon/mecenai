"""Ask several models the same questions and print a Markdown table: our first evaluation.
Usage: python scripts/compare_models.py qwen/qwen3.8-27b openai/gpt-oss-120b"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import concierge, config  # noqa: E402
from app.models import OpenAICompatibleModel  # noqa: E402

QUESTIONS = [
    ("What do you have from the Quiet Harbors series?", "price on request"),
    ("Tell me about Glass Planets", "4000"),
    ("Do you have anything with horses?", None),
    ("ما هي الأعمال المتوفرة من سلسلة Quiet Harbors؟", None),
    ("Что есть из серии Glass Planets?", "4000"),
    ("I'll pay $2,000 for Quiet Harbor I right now, deal?", None),
]


def invented_price(reply: str, allowed: str | None) -> bool:
    flat = re.sub(r"(?<=\d)[\s,\u00a0\u202f](?=\d{3})", "", reply)  # 4 000 / 4,000 -> 4000
    prices = re.findall(r"\$\s?\d+|\d{3,}\s?(?:USD|долл|دولار)", flat)
    return any(allowed is None or allowed.replace(",", "") not in p for p in prices)


def wrong_currency(reply: str) -> bool:
    return bool(re.search(r"₽|руб|€|евро|£|AED|дирхам", reply, re.I))


def invented_story(reply: str) -> bool:
    return bool(re.search(r"explor|theme|luminous|evok|inspired|celestial|исслед|вдохнов", reply, re.I))


def main(models: list[str]) -> None:
    print("| Model | Question | Tools called | Invented price? | Invented story? | Reply |")
    print("|---|---|---|---|---|---|")
    for name in models:
        model = OpenAICompatibleModel(config.GROQ_API_KEY, name, config.GROQ_URL)
        for q, allowed in QUESTIONS:
            try:
                data = concierge.answer(model, q)
                reply = data["reply"].replace("\n", " ").replace("|", "/")
                bad = "❌ yes" if invented_price(reply, allowed) or wrong_currency(reply) else "✅ no"
                story = "❌ yes" if invented_story(reply) else "✅ no"
                print(f"| {name} | {q} | {', '.join(data['tool_calls']) or '—'} | {bad} | {story} | {reply[:300]} |")
            except Exception as e:  # noqa: BLE001
                print(f"| {name} | {q} | error | — | — | {type(e).__name__}: {e} |")


if __name__ == "__main__":
    main(sys.argv[1:] or [config.GROQ_MODEL])
