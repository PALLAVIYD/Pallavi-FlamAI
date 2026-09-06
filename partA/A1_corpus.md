# A1 — Eval Corpus Description

## Corpus Size

All four files contain **1012 lines** each (FLORES-200 devtest split).

| file | lines |
|---|---|
| `data/flores/eng.txt` | 1012 |
| `data/flores/hin.txt` | 1012 |
| `data/flores/kan.txt` | 1012 |
| `data/flores/tam.txt` | 1012 |

## Source

**FLORES-200 devtest** — downloaded directly from Meta's CDN:
`https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz`

Files used from `flores200_dataset/devtest/`:

| language | FLORES-200 file | lines |
|---|---|---|
| English | `eng_Latn.devtest` | 1012 |
| Hindi | `hin_Deva.devtest` | 1012 |
| Kannada | `kan_Knda.devtest` | 1012 |
| Tamil | `tam_Taml.devtest` | 1012 |

## Domain

Formal, Wikipedia-style, lightly edited encyclopaedic text. Sentences are drawn from Wikipedia articles that have been professionally translated by bilingual annotators — the gold-standard alignment property is preserved (line N is the same sentence in every language file).

## What FLORES-200 Can't Tell You

1. **No colloquial or code-mixed text.** Real Indic LLM traffic often mixes scripts (Hinglish, Kanglish). Fertility on formal FLORES sentences will underestimate token inflation on chat-style or code-switched input.
2. **Single domain.** All sentences are encyclopedia-style prose. Instruction following, creative writing, and technical Q&A will have different token distributions.
3. **~1012 lines.** Statistically sufficient for a stable mean, but not large enough to detect tail-distribution effects (very long, very short, or emoji-heavy sentences).
4. **No spoken-language orthographic variation.** Users in the wild often misspell or use phonetic spelling; neither tokenizer was evaluated on that register.
