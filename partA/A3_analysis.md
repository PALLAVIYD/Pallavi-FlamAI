# A3 — Corrected Analysis and Denominator Reasoning

## Data: Three Fertility Tables (FLORES-200 devtest, 1012 sentences)

### GPT-2 tokenizer (baseline, no lowercase)

```
tokenizer: gpt2   lowercase: False
lang      tok/word  tok/grapheme    tok/byte  tok/sentence
----------------------------------------------------------
eng           1.24         0.207       0.207         26.72
hin           7.87         2.341       0.595        198.31
kan          23.02         4.065       0.979        363.01
tam          25.25         4.215       0.996        415.19

ratios vs eng:
  hin tok_per_word: 6.32x  tok_per_grapheme: 11.31x  tok_per_byte: 2.88x  tok_per_sentence: 7.42x
  kan tok_per_word: 18.50x tok_per_grapheme: 19.64x  tok_per_byte: 4.73x  tok_per_sentence: 13.58x
  tam tok_per_word: 20.29x tok_per_grapheme: 20.36x  tok_per_byte: 4.82x  tok_per_sentence: 15.54x
```

### MuRIL tokenizer (google/muril-base-cased — Indic-aware)

```
tokenizer: hf:google/muril-base-cased   lowercase: False
lang      tok/word  tok/grapheme    tok/byte  tok/sentence
----------------------------------------------------------
eng           1.27         0.211       0.211         27.25
hin           1.25         0.374       0.096         31.55
kan           1.84         0.327       0.079         29.03
tam           1.75         0.293       0.070         28.86

ratios vs eng:
  hin tok_per_word: 0.99x  tok_per_grapheme: 1.77x  tok_per_byte: 0.45x  tok_per_sentence: 1.16x
  kan tok_per_word: 1.45x  tok_per_grapheme: 1.55x  tok_per_byte: 0.38x  tok_per_sentence: 1.07x
  tam tok_per_word: 1.38x  tok_per_grapheme: 1.39x  tok_per_byte: 0.33x  tok_per_sentence: 1.06x
```

### GPT-2 lowercased (quantifying Bug 2 at corpus scale)

```
tokenizer: gpt2   lowercase: True
lang      tok/word  tok/grapheme    tok/byte  tok/sentence
----------------------------------------------------------
eng           1.29         0.214       0.214         27.66   (+0.05 tok/word vs non-lowercased)
hin           7.87         2.341       0.595        198.32   (unchanged — no casing in Devanagari)
kan          23.02         4.066       0.979        363.03   (unchanged — no casing in Kannada)
tam          25.25         4.215       0.996        415.21   (unchanged — no casing in Tamil)
```

---

## 1. Tokenizer Comparison: GPT-2 vs MuRIL

The contrast is stark. Under GPT-2, Hindi's `tok/word` ratio is **6.32× English**. Under MuRIL, it is **0.99× English** — effectively *equal*. The same collapse happens for Kannada (18.50× → 1.45×) and Tamil (20.29× → 1.38×).

**This directly falsifies the original report's claim:** "Root cause: Hindi simply has more Unicode characters per word, so *any tokenizer* will struggle. This is a property of the script, not the tokenizer."

It is demonstrably *not* a property of the script. It is a property of GPT-2's vocabulary, which was trained primarily on English text and lacks Devanagari/Kannada/Tamil subword units. When an Indic-aware tokenizer (MuRIL) is used, the `tok/word` gap shrinks by 84–93% for all three Indic languages.

**`tok/sentence` gap under MuRIL**: Hindi 31.55 vs English 27.25 → **1.16×** (down from 7.42× under GPT-2). Kannada: **1.07×**; Tamil: **1.06×**. These are essentially equal sentence lengths in token space — the Indic languages are actually slightly *more* concise per sentence than English under MuRIL, because MuRIL's vocabulary models their morphology efficiently.

---

## 2. Denominator Comparison

| metric | GPT-2 worst language | GPT-2 ratio | MuRIL worst language | MuRIL ratio |
|---|---|---|---|---|
| tok/word | Tamil | 20.29× | Tamil | 1.38× |
| tok/grapheme | Tamil | 20.36× | Tamil | 1.39× |
| tok/byte | Tamil | 4.82× | Hindi | 0.45× |
| tok/sentence | Tamil | 15.54× | Hindi | 1.16× |

**Key observations:**
- `tok/word` and `tok/grapheme` agree almost perfectly in their ranking and magnitude under both tokenizers. This is because the two denominators are strongly correlated (grapheme count ≈ proportional to word count for the same text).
- `tok/byte` produces a dramatically different picture. Under MuRIL, Hindi, Kannada, and Tamil are all **cheaper** per byte than English (0.45×, 0.38×, 0.33×) — because Indic scripts encode densely in Unicode (2–4 bytes per character) and MuRIL's vocabulary handles them efficiently.
- Under GPT-2, `tok/byte` still shows a large gap (2.88–4.82×) but it is *substantially smaller* than the `tok/word` gap (6.32–20.29×), confirming that some of the `tok/word` gap was always denominator inflation, not real token cost.

---

## 3. Which Denominator Should Drive Routing / Cost Decisions?

**Recommendation: `tok/byte` with an Indic-aware tokenizer.**

Routing and cost decisions depend on **total tokens processed per request**, which is a function of input content, not language category. The correct question is: "given N bytes of user input, how many tokens will be processed?"

- `tok/word` fails because "word" means different things across languages (agglutinative Indic words encode what English spreads over multiple words). The denominator is language-specific.
- `tok/grapheme` has the same structural problem: grapheme count per meaning unit varies by language and morphology.
- `tok/byte` holds the input size constant in a language-agnostic way. A byte is a byte regardless of the script. All downstream I/O (network, storage, KV cache budget via prompt length) is ultimately byte-bounded.
- `tok/sentence` works well for sentence-aligned benchmarks like FLORES (where sentence N is semantically identical across languages) but cannot be used for production routing where sentences differ in content.

**Therefore: estimate routing cost as `(input bytes) × tok/byte_for_language_and_tokenizer`.**

---

## 4. Combined Conclusion

**84–93% of the originally reported Hindi/Indic fertility gap is a tokenizer-training artifact** — it disappears when you switch from GPT-2 to MuRIL. The remaining gap (1.06–1.16× on `tok/sentence` under MuRIL) is a real but small structural difference, not the 6–20× advertised in the original report.

The correct cost metric is **`tok/byte`** (not `tok/word`), because it is language-agnostic and maps directly to what the serving system actually processes. Under this metric and with an Indic-aware tokenizer:

- Hindi costs **0.45×** the per-byte rate of English — *cheaper*, not 5.89× more expensive.
- Tamil costs **0.33×** per byte.
- The original report's recommendation ("budget 6× serving cost for Hindi") overstates the true cost by more than an order of magnitude when the right tokenizer and denominator are used.
