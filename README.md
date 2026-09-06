# Tokenizer & Serving Audit — Submission

A complete audit of tokenizer fertility and LLM serving efficiency, submitted as part of the Flam AI technical assessment.

## Repository Structure

```
your-submission/
├── NOTEBOOK.md          # Chronological lab notebook of all steps taken
├── AI_USAGE.md          # Disclosure of AI assistance used
├── partA/               # Tokenizer fertility audit
│   ├── A1_corpus.md     # Corpus description & preparation
│   ├── A2_audit.md      # Raw audit findings
│   ├── A3_analysis.md   # Corrected analysis & discussion
│   ├── A4_memo.md       # Memo summarizing key findings
│   ├── audit_findings.py
│   └── fertility_v2.py
├── partB/               # Serving efficiency calculations
│   ├── B_writeup.md     # Written answers & calculations
│   ├── b1_kv_cache.py
│   └── b3_goodput.py
└── partC/
    └── memo.md          # Architecture recommendation memo
```

## Parts Overview

### Part A — Tokenizer Fertility Audit
Compares tokenizer fertility (tokens-per-word) across three tokenizers (GPT-2, MuRIL, NLLB-200) on a multilingual FLORES-200 corpus spanning English, Hindi, Kannada, and Tamil. Identifies the original bug in `fertility_v0`, corrects it in `fertility_v2.py`, and documents the impact on reported metrics.

### Part B — Serving Efficiency
Calculates KV-cache memory requirements (B1) and goodput under SLA constraints (B3) for a 7B-parameter LLM deployment. All calculations are shown with derivations.

### Part C — Architecture Memo
Recommends a tokenizer strategy for a multilingual product serving Indic languages, with trade-off analysis between GPT-2, MuRIL, and NLLB-200.

## Reproducibility

Scripts require Python 3.10+ with:
```
pip install tiktoken transformers sentencepiece datasets
```

All output files are included in the repo — scripts do not need to be re-run to verify answers.
