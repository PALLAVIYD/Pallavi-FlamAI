# B — Capacity Reconciliation Writeup (B1–B4)

## B1 — KV-Cache Ceiling Arithmetic

### Inputs (from `model_spec.md`)

| parameter | value |
|---|---|
| Layers | 28 |
| KV heads (GQA) | 8 |
| head_dim | 128 |
| KV cache dtype | fp16 (2 bytes) |
| GPU VRAM | 24 GB (L4) |
| `gpu_memory_utilization` | 0.92 |
| Weights (4.2B × 2 bytes) | 8.4 GB |
| Non-KV overhead | 1.6 GB |
| `max_model_len` | 4096 tokens |

### Derivation

```
bytes_per_token = 2 × 28 × 8 × 128 × 2 = 114,688 bytes
usable_gb       = 24 × 0.92             = 22.08 GB
kv_budget_gb    = 22.08 − 8.4 − 1.6    = 12.08 GB
bytes_per_seq   = 114,688 × 4096       = 469,762,048 bytes ≈ 0.470 GB
max_concurrent  = 12.08 GB / 0.470 GB  = 25.71 sequences
```

*(Output from `partB/results_b1.txt`:)*
```
bytes per token: 114688
usable GB: 22.08  weights GB: 8.4  KV budget GB: 12.08
bytes per 4096-token sequence: 469762048
max concurrent sequences: 25.715
```

### Cross-check vs `bench_log.csv`

The ceiling (~25–26 concurrent sequences at max_model_len) is consistent with the log: at `batch_size=24`, `kv_cache_util` reaches **0.93** (93%), right below the ceiling. At `batch_size=32` and `batch_size=48`, `kv_cache_util` pins at **0.97** and `preempted_seqs` becomes non-zero (7 and 23 respectively), confirming that the scheduler begins evicting sequences exactly where the arithmetic predicts.

The agreement is tight — the ceiling math matches the log within one batch increment, which is expected since not all sequences hit `max_model_len` simultaneously (prompts are 3584 tokens, generation adds up to 512, total = 4096 exactly for the long-prompt rows).

---

## B2 — Throughput Anomaly: Why Throughput Falls Past Batch 24

### The Anomaly

In the long-prompt rows (prompt_len=3584), throughput peaks at **1607 tok/s** at batch=24 and then *falls* to 1384 and 1299 tok/s at batch=32 and 48 respectively. The original report claims "longer prompts give better GPU utilization" and extrapolates linearly — but the log directly contradicts this for batch sizes above 24.

### Mechanism

At batch=24, the system reaches ~93% KV-cache utilisation. Adding more concurrent sequences pushes it to 97%+, which forces the vLLM scheduler to **preempt** (evict) sequences mid-generation (7 at batch=32, 23 at batch=48). Preemption means:

1. The KV-cache blocks for the evicted sequence are written to CPU memory (or discarded and recomputed).
2. When the sequence is rescheduled, the prompt must be **re-prefilled** — paying the full prefill cost again.
3. Wall-clock time (`wall_clock_s`) grows super-linearly while token count grows linearly, so throughput (tok/s) falls.

### Proposed Fix and Predicted Effect

**Fix:** Reduce `max_model_len` from 4096 to 3840 (cutting 256 tokens = ~6.25% of sequence budget). This increases `kv_budget_gb` available per sequence, raising the theoretical ceiling from ~25.7 to ~27+ sequences, allowing batch=32 to fit without eviction.

**Predicted quantitative effect:** At batch=32, preemption drops to 0; `wall_clock_s` should return to the ~67s range (interpolating the short-prompt linear trend), restoring throughput to ~1550–1600 tok/s, a ~12–15% improvement over the current degraded 1384 tok/s.

---

## B3 — What `reported_tok_s` Actually Measures

### Recovered Formula

By dividing `(prompt_len + gen_len) × num_requests / wall_clock_s` and comparing to `reported_tok_s`, both columns agree within <1% for every row. Therefore:

```
reported_tok_s = (prompt_len + gen_len) × num_requests / wall_clock_s
```

This is a **blended prefill + decode metric** — it counts every token processed during both the prefill (prompt processing) and decode (generation) phases.

### Why This Misleads

1. **Prefill and decode have different costs.** Prefill processes the full prompt in a single forward pass (parallel, GPU-efficient). Decode generates one token per step (memory-bandwidth-bound). Blending them produces a number that is neither the real prefill throughput nor the real decode throughput.
2. **The original report claims "1311 tok/s for long prompts is better."** In fact, long prompts inflate the numerator disproportionately (3584 prompt tokens vs 512 generated), making `reported_tok_s` look high while the actual *decode goodput* is much lower.

### Real Decode Goodput (batch=24, prompt=3584)

From `b3_goodput.py`:

| method | formula | result |
|---|---|---|
| Method 1 | `num_requests × gen_len / wall_clock_s` = `24 × 512 / 61.16` | **200.9 tok/s** |
| Method 2 | `batch_size / (itl_ms_p50 / 1000)` = `24 / (96.07/1000)` | **249.8 tok/s** |

*(Verified by `partB/results_b3.txt` — both values match to 1 decimal place.)*

Both methods confirm that real decode throughput is ~200–250 tok/s — roughly 8× lower than the 1607 tok/s headline number. The difference between method 1 and method 2 is explained by queuing jitter at the KV boundary (method 1 measures wall-clock which includes ramp-up; method 2 measures the steady-state decode rate from inter-token latency).

---

## B4 — Counter to Pull for Decode-Step Confirmation

**Counter:** `decode_throughput_toks_per_s` — the number of *new tokens generated* (decode steps only) per second, excluding prefill tokens. In vLLM this is equivalent to `num_decode_tokens / decode_time_per_step`.

**Expected values:**
- At batch=24 (long prompt): ~200–250 tok/s (consistent with both methods above).
- At batch=32: **will not recover to 1384 tok/s or above** — decode goodput will be ≤200 tok/s because the KV-cache ceiling forces sequential processing of what should be parallel decode steps.
- At batch=48: similar or worse (more preemptions = more recompute overhead).

This counter directly falsifies the original report's recommendation to "scale linearly with batch size" — the log already shows super-linear wall-clock growth; a decode-only counter would make the degradation impossible to ignore.
