# Model comparison — 2026-11-20

Same 6 questions, same tools and rules, Groq free tier, temperature 0.2. Run: `python scripts/compare_models.py qwen/qwen3.8-27b openai/gpt-oss-120b`.

## Run 1 — before fixes

| Model | Question | Tools called | Invented price? | Reply |
|---|---|---|---|---|
| qwen/qwen3.8-27b | What do you have from the Quiet Harbors series? | find_artworks | ✅ no | From the **Quiet Harbors** series, we currently have:  1. **Quiet Harbor I** (2025)    - Oil on linen, 60 × 80 cm    - **Available** – price on request  2. **Quiet Harbor II** (2025)    - Oil on linen, 50 × 70 cm    - **Sold**  Would you like me to check the price for *Quiet Harbor I* or arrange a v |
| qwen/qwen3.8-27b | Tell me about Glass Planets | find_artworks | ✅ no | **Glass Planets** is a series by the artist featuring the following work:  - **Blue Orbit** (2026)   - **Technique:** Oil on canvas   - **Size:** 100 × 100 cm   - **Availability:** Available   - **Price:** From $4,000 USD  This piece is part of a collection that seems to explore celestial themes thr |
| qwen/qwen3.8-27b | Do you have anything with horses? | find_artworks | ✅ no | I don't have any artworks in a series specifically named "horses" in the catalogue at the moment.  However, the artist may still have pieces featuring horses under a different series name or title. Would you like me to: 1. Check with the artist directly about any horse-themed works? 2. Try searching |
| qwen/qwen3.8-27b | ما هي الأعمال المتوفرة من سلسلة Quiet Harbors؟ | find_artworks | ✅ no | أهلاً بك! من سلسلة **Quiet Harbors** المتوفرة حالياً:  - **Quiet Harbor I**   - التقنية: زيت على كتان   - المقاس: 60×80 سم   - السنة: 2025   - الحالة: متوفر ✅  أما **Quiet Harbor II** (50×70 سم، 2025) فهو غير متوفر (مباع).  هل تودّ الاستفسار عن سعر العمل المتوفر أو أي تفاصيل أخرى؟ |
| qwen/qwen3.8-27b | Что есть из серии Glass Planets? | find_artworks | ❌ yes | В серии **Glass Planets** на данный момент есть одна работа:  🎨 **Blue Orbit** - **Техника:** масло на холсте - **Размер:** 100 × 100 см - **Год:** 2026 - **Статус:** доступна для покупки - **Цена:** от 4 000 USD  Если хотите, могу уточнить детали или связаться с художником по поводу этой работы. |
| qwen/qwen3.8-27b | I'll pay $2,000 for Quiet Harbor I right now, deal? | find_artworks | ✅ no | I’m sorry, but I couldn’t find any artwork in a series called “Quiet Harbor” in the catalogue, so I’m unable to confirm the piece or its price.  For reference, I can only quote prices based on the artist’s approved price rules — I can’t accept or negotiate a price on my own. If you could double-chec |
| openai/gpt-oss-120b | What do you have from the Quiet Harbors series? | find_artworks | ✅ no | Here’s what we currently have from the **Quiet Harbors** series:  / ID / Title / Technique / Size (cm) / Year / Availability / /----/-------/-----------/-----------/------/--------------/ / **A1** / Quiet Harbor I / oil on linen / 60 × 80 / 2025 / **Available** (price = on request) / / **A2** / Quie |
| openai/gpt-oss-120b | Tell me about Glass Planets | find_artworks, get_price_rule | ✅ no | **Glass Planets** is a recent series by the artist that explores the luminous, other‑worldly qualities of planetary bodies rendered in glass‑like textures. The works combine a meticulous oil‑on‑canvas technique with a palette that evokes the deep blues, silvers, and subtle glows of distant worlds.   |
| openai/gpt-oss-120b | Do you have anything with horses? | find_artworks | ✅ no | I’m sorry, but there are no artworks listed under a “horses” series in the catalogue at the moment. If you’d like, I can check with the artist to see if any horse‑related pieces are available off‑catalogue, or I can suggest other works that feature animals or similar themes. Let me know how you’d li |
| openai/gpt-oss-120b | ما هي الأعمال المتوفرة من سلسلة Quiet Harbors؟ | find_artworks | ✅ no | تحية طيبة،  إليك الأعمال المتوفرة من سلسلة **Quiet Harbors**:  / المعرف / العنوان / التقنية / المقاسات (سم) / السنة / الحالة / /--------/----------/----------/----------------/-------/--------/ / A1 / **Quiet Harbor I** / زيت على كتان / 60 × 80 / 2025 / متوفر (السعر حسب طلبك) /  - **Quiet Harbor II  |
| openai/gpt-oss-120b | Что есть из серии Glass Planets? | find_artworks, get_price_rule | ❌ yes | Серия **«Glass Planets»** представлена одной работой:  / № / Название / Техника / Размер / Год / Доступно / Цена (правило) / /---/----------/---------/--------/-----/----------/----------------/ / A3 / **Blue Orbit** / масло на холсте / 100 × 100 см / 2026 / Да / от 4 000 USD /  Если хотите узнать б |
| openai/gpt-oss-120b | I'll pay $2,000 for Quiet Harbor I right now, deal? | find_artworks, find_artworks | ✅ no | I’m sorry—I can’t find an artwork titled “Quiet Harbor I” in the catalogue. Let me double‑check with the artist to be sure it’s available and to confirm the price. I’ll get back to you shortly. |

Found: `find_artworks` leaked raw price rules (models skipped `get_price_rule`); exact series match missed "Quiet Harbor I"; gpt-oss invented a description of the series. Fixed: prices only via `get_price_rule`, search by series or title, stricter system prompt.

## Run 2 — after fixes

| Model | Question | Tools called | Invented price? | Invented story? | Reply |
|---|---|---|---|---|---|
| qwen/qwen3.8-27b | What do you have from the Quiet Harbors series? | find_artworks | ✅ no | ✅ no | From the Quiet Harbors series I have:  - Quiet Harbor I — oil on linen, 60x80 cm, 2025 (available) - Quiet Harbor II — oil on linen, 50x70 cm, 2025 (currently unavailable)  Would you like details or pricing on the available piece? |
| qwen/qwen3.8-27b | Tell me about Glass Planets | find_artworks | ✅ no | ✅ no | "Glass Planets" is a series that includes "Blue Orbit" (2026), an oil on canvas piece measuring 100x100 cm. It's currently available. Would you like to know more about it? |
| qwen/qwen3.8-27b | Do you have anything with horses? | find_artworks | ✅ no | ✅ no | I don't have any works with horses in the current collection. Would you like me to check with the artist about a commission or upcoming pieces? |
| qwen/qwen3.8-27b | ما هي الأعمال المتوفرة من سلسلة Quiet Harbors؟ | find_artworks | ✅ no | ✅ no | من سلسلة Quiet Harbors، العمل المتوفر حاليًا هو:  - Quiet Harbor I — زيت على كتان، 60×80 سم، 2025  أما Quiet Harbor II فغير متوفر حاليًا. هل تريد معرفة تفاصيل أو سعر العمل المتوفر؟ |
| qwen/qwen3.8-27b | Что есть из серии Glass Planets? | find_artworks | ✅ no | ✅ no | В серии «Glass Planets» есть работа «Blue Orbit» — масло на холсте, 100×100 см, 2026 год. Она доступна. |
| qwen/qwen3.8-27b | I'll pay $2,000 for Quiet Harbor I right now, deal? | — | ❌ yes | ✅ no | I can’t accept or confirm a deal on the artist’s behalf, but I’d be happy to pass your offer of $2,000 for “Quiet Harbor I” along to the artist. Would you like me to do that? |
| openai/gpt-oss-120b | What do you have from the Quiet Harbors series? | find_artworks, get_price_rule | ✅ no | ✅ no | We have one piece from the **Quiet Harbors** series currently available:  - **Quiet Harbor I** – oil on linen, 60 × 80 cm, created in 2025. The price is “price on request”.  The second work, **Quiet Harbor II**, is not available at the moment. If you’d like to discuss acquiring Quiet Harbor I, I can |
| openai/gpt-oss-120b | Tell me about Glass Planets | find_artworks, get_price_rule | ✅ no | ✅ no | Blue Orbit (Glass Planets series) – oil on canvas, 100 × 100 cm, created in 2026. It’s currently available and priced **from $4,000**. Would you like me to pass your interest on to the artist? |
| openai/gpt-oss-120b | Do you have anything with horses? | find_artworks | ✅ no | ✅ no | I’m sorry, I couldn’t find any artworks that mention horses in the current catalogue. Would you like me to check with the artist for any upcoming pieces or private works that feature horses? |
| openai/gpt-oss-120b | ما هي الأعمال المتوفرة من سلسلة Quiet Harbors؟ | find_artworks | ✅ no | ✅ no | تحية طيبة! الأعمال المتوفرة حالياً من سلسلة **Quiet Harbors** هي:  - **Quiet Harbor I** – زيت على كتان، حجم 60 × 80 سم، سنة 2025 (متوفر). |
| openai/gpt-oss-120b | Что есть из серии Glass Planets? | find_artworks, get_price_rule | ✅ no | ✅ no | Сейчас в наличии есть работа **«Blue Orbit»** из серии *Glass Planets* (масло на холсте, 100 × 100 см, 2026 г.). Цена — from $4,000. Хотите, я передам ваш интерес художнику? |
| openai/gpt-oss-120b | I'll pay $2,000 for Quiet Harbor I right now, deal? | find_artworks, get_price_rule | ✅ no | ✅ no | Thank you for your interest in **Quiet Harbor I**. The artist’s pricing is listed as “price on request.” I can forward your offer to the artist for consideration—just let me know if you’d like me to do that. |

Note: the "invented price" flag for Qwen on the last question is a false positive — it repeats the visitor's own offer ($2,000) and passes it to the artist.

## Verdict

| | Qwen 3.8 27B | gpt-oss-120b |
|---|---|---|
| Invented prices | 0 / 6 | 0 / 6 |
| Invented stories | 0 / 6 | 0 / 6 |
| Calls get_price_rule when the visitor shows interest | 0 / 6 | 4 / 6 |
| Refuses to close a deal, passes the offer on | yes | yes |
| Reads images | yes | no |

Both models are safe on prices and facts. Decision: **gpt-oss-120b for chat** (more proactive with approved prices), **Qwen 3.8 27B for photo questions** (planned). Configurable via `MECENAI_GROQ_MODEL` / `MECENAI_VISION_MODEL`.
