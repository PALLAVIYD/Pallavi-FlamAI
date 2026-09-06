# A4 — Recommendation Memo

**To:** Engineering / ML Platform team  
**From:** Tokenizer & Serving Audit  
**Re:** Indic language serving cost and routing recommendation

---

## Corrected Headline Numbers (FLORES-200 devtest, 1012 sentences)

### GPT-2 tokenizer (baseline — matches original report's tokenizer):

| lang | tok/word | tok/grapheme | tok/byte | tok/sentence |
|---|---|---|---|---|
| eng | 1.24 | 0.207 | 0.207 | 26.72 |
| hin | 7.87 | 2.341 | 0.595 | 198.31 |
| kan | 23.02 | 4.065 | 0.979 | 363.01 |
| tam | 25.25 | 4.215 | 0.996 | 415.19 |

### MuRIL tokenizer (google/muril-base-cased — Indic-aware):

| lang | tok/word | tok/grapheme | tok/byte | tok/sentence |
|---|---|---|---|---|
| eng | 1.27 | 0.211 | 0.211 | 27.25 |
| hin | 1.25 | 0.374 | 0.096 | 31.55 |
| kan | 1.84 | 0.327 | 0.079 | 29.03 |
| tam | 1.75 | 0.293 | 0.070 | 28.86 |

*(Full tables and ratio breakdowns in `partA/results/fertility_gpt2.txt` and `partA/results/fertility_muril.txt`.)*

---

## Routing Recommendation

**Use `tok/byte` as the primary cost-modelling metric**, not `tok/word`.

Byte count is language-agnostic: a byte budget has the same physical meaning for every language, whereas "words" differ per language's morphological complexity. Routing and quota decisions should be driven by estimated byte cost of the input, not word count.

**Do not assume a flat 6× Hindi cost multiplier.** The original report's 5.89× number is a GPT-2 `tok/word` number under incorrect methodology (lowercasing + `split(' ')`). Under the corrected methodology, and especially under an Indic-aware tokenizer (MuRIL), the `tok/byte` gap is substantially smaller — meaning a significant portion of the observed gap is a *tokenizer-training artifact*, not an inherent property of the script.

If you must deploy a single tokenizer, prefer one with native Indic vocabulary coverage (e.g., MuRIL or a purpose-trained Indic LLM tokenizer) rather than GPT-2's BPE. This alone will reduce the per-token overhead for Hindi/Kannada/Tamil without any routing changes.

---

## Biggest Caveat

This audit used a single domain (formal Wikipedia-style FLORES-200 sentences) and only two tokenizers. Real Indic LLM traffic includes:
- Code-mixed text (Hinglish, Kanglish)
- Colloquial and transliterated input
- Highly variable sentence lengths

The `tok/byte` estimate should be treated as a lower bound on production token inflation for conversational Indic traffic.

---

## Recommended Production Metric to Monitor

**Live `tok/byte` per language**, computed from actual inference logs.

Alert if any language's live `tok/byte` drifts more than ±20% from the offline FLORES-200 estimate — this signals distribution shift that warrants re-evaluation. This metric is directly computable from token counts and raw request byte sizes already logged by most serving frameworks.
