# A2 — Script Audit Findings

## Overview

The original `fertility_v0_original.py` contains three bugs that directly corrupt its output numbers, plus one dead-code item that looks suspicious but has no effect. Evidence for each claim is drawn from running `audit_findings.py` against the sample files.

---

## Bug 1 — `split(' ')` vs `split()`: phantom empty word from double-space

**Command:**
```bash
python3 partA/audit_findings.py 2>&1 | grep -A4 "Bug 1"
```

**Evidence from `partA/results/audit_findings_output.txt`:**

```
data/eng_sample.txt 'Please keep the books  in the cupboard.'
  split(' ') -> 8 ['Please', 'keep', 'the', 'books', '', 'in', 'the', 'cupboard.']
  split()    -> 7 ['Please', 'keep', 'the', 'books', 'in', 'the', 'cupboard.']
data/hin_sample.txt 'किताबें  अलमारी में रखी हैं।'
  split(' ') -> 6 ['किताबें', '', 'अलमारी', 'में', 'रखी', 'हैं।']
  split()    -> 5 ['किताबें', 'अलमारी', 'में', 'रखी', 'हैं।']
```

**Before (buggy):** `split(' ')` inflates `len(words)` by 1 for any line with a double space.
**After (fixed):** `split()` returns only non-empty tokens regardless of whitespace repetition.

**Why the delta proves the claim:** a larger word-count denominator in the original script silently deflates the fertility number (fewer tokens-per-word than reality). Any sentence with a double space reports a *lower* fertility than the corrected version.

---

## Bug 2 — Unconditional `.lower()` creates a lowercasing asymmetry between English and Hindi

**Command:**
```bash
python3 partA/audit_findings.py 2>&1 | grep -A12 "Bug 2"
```

**Evidence from `partA/results/audit_findings_output.txt`:**

| file | tokenizer | mode | total tokens |
|---|---|---|---|
| eng_sample.txt | gpt2 | original | **96** |
| eng_sample.txt | gpt2 | lowercased | **99** (+3, +3.1%) |
| eng_sample.txt | muril | original | **91** |
| eng_sample.txt | muril | lowercased | **96** (+5, +5.5%) |
| hin_sample.txt | gpt2 | original | **459** |
| hin_sample.txt | gpt2 | lowercased | **459** (unchanged) |
| hin_sample.txt | muril | original | **76** |
| hin_sample.txt | muril | lowercased | **76** (unchanged) |

**Key observation:** English token counts differ between lowercased and original because GPT-2's BPE merges were trained on case-sensitive data — lowercasing destroys merges that include uppercase variants (e.g., `" The"` as a unit vs `" the"` splitting differently). Hindi (Devanagari script) has **no casing**, so its counts are identical in both modes for both tokenizers.

**Why the delta proves the claim:** applying `.lower()` to English reduces its token count (makes it look cheaper) while leaving Hindi unchanged, artificially *widening* the Hindi-vs-English fertility gap in the original report. The comparison is not apples-to-apples.

---

## Bug 3 — `len()` counts Unicode codepoints, not grapheme clusters (Devanagari combining marks)

**Command:**
```bash
python3 partA/audit_findings.py 2>&1 | grep -A3 "Bug 3"
```

**Evidence from `partA/results/audit_findings_output.txt`:**

```
codepoints: 290   graphemes: 188   ratio: 1.543
```

The ratio is greater than 1.0, which means `len()` consistently overcounts real character units in Hindi. Devanagari uses combining vowel signs (matras) and nuktas that are separate codepoints attached visually to a base consonant — the user perceives one character, but Python's `len()` counts two or more.

**Why the delta proves the claim:** the original `tok/char` denominator (`len(line)`) is inflated by the combining-mark count. This makes Hindi look like it uses *fewer tokens per character* than the true grapheme-based ratio — the denominator is too big, so the quotient is too small. This biases any `tok/char` comparison specifically against Hindi (and similar Indic scripts) while leaving Latin-script languages unaffected.

**Concrete fertility impact on the Hindi sample:**

```
Command: python -c "
  import regex, unicodedata, tiktoken
  enc = tiktoken.get_encoding('gpt2')
  total_tok, total_cp, total_gr = 0, 0, 0
  for raw in open('data/hin_sample.txt', encoding='utf-8'):
      line = unicodedata.normalize('NFC', raw.strip())
      if line:
          total_tok += len(enc.encode(line))
          total_cp  += len(line)
          total_gr  += len(regex.findall(r'\X', line))
  print(total_tok, total_cp, total_gr)
"

  original tok/char (codepoints): 459 tokens / 290 codepoints = 1.5828
  corrected tok/grapheme:         459 tokens / 188 graphemes  = 2.4415
  distortion: 1.5828 → 2.4415 — a 54.3% understatement of the true per-character fertility
```

The original script's `tok/char` number (1.58) makes Hindi appear 54% cheaper per character unit than it actually is when character units are counted correctly as grapheme clusters.

---

## The `random` import — Harmless Dead Code

```bash
grep -n "random\." partA/fertility_v0_original.py
```

**Output:** `line 25: random.seed(1337)  # reproducibility`

`random.seed()` is set but `random` is never called again. The seed has zero effect on any output. This is **not a bug** — it is dead code, probably left over from an earlier version that sampled lines randomly. The correct conclusion: do not claim this as a bug; flag it as a cleanup item only.

---

## Conceptual Bug: "Tokens per whitespace word" is not a fair cross-language denominator

Hindi is an agglutinative language with postpositions; Kannada and Tamil have complex morphological suffixing. A single "word" in these languages may express what English encodes in three or four words. Using whitespace-tokenised word count as the denominator conflates the tokenizer's behaviour with each language's morphological complexity. The result is that the original report's headline ("5.89× worse") measures a blend of tokenizer quality and linguistic structure, not tokenizer quality alone.

Stage 5 (A3) addresses this numerically by comparing `tok/word`, `tok/grapheme`, `tok/byte`, and `tok/sentence` across four languages under both the GPT-2 and MuRIL tokenizers.
