# AI_USAGE.md — AI Assistance Disclosure

## Overview

This audit was executed with the assistance of an AI coding agent (Antigravity/Claude). This document discloses what the AI did and did not do.

## What the AI did

- **Executed the runbook:** Ran all 10 stages in order following `AGENT_RUNBOOK_ONESHOT.md`.
- **Environment setup:** Created the Python venv, installed all required packages.
- **Corpus acquisition:** Identified that `facebook/flores` is gated on HuggingFace; downloaded the FLORES-200 dataset directly from Meta's public CDN (`dl.fbaipublicfiles.com`).
- **Script execution:** Ran `audit_findings.py`, `fertility_v2.py` (3 configurations), `b1_kv_cache.py`, and `b3_goodput.py` on real data and captured outputs.
- **Debugging:** Fixed a Windows-specific `UnicodeEncodeError` (added `PYTHONIOENCODING=utf-8`) and replaced a `subprocess.run(["grep", ...])` call (which doesn't work on Windows) with a pure Python equivalent.
- **Document writing:** Wrote `A1_corpus.md`, `A2_audit.md`, `A3_analysis.md`, `A4_memo.md`, `B_writeup.md`, `partC/memo.md`, and `NOTEBOOK.md`.

## What the AI did NOT do

- **Fabricate outputs.** All numbers in the analysis documents are taken directly from the script output files in `partA/results/` and `partB/results_*.txt`. No numbers were made up.
- **Write the core scripts from scratch.** `fertility_v2.py`, `audit_findings.py`, `b1_kv_cache.py`, and `b3_goodput.py` were transcribed verbatim from the runbook (with the Windows `grep` fix noted above).
- **Change the original script.** `partA/fertility_v0_original.py` is an untouched copy of the starter kit's `fertility.py`.

## AI tool used

Antigravity AI coding agent (Google DeepMind) with Claude Sonnet 4.6 (Thinking) model.
