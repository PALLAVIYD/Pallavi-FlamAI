import csv
rows = list(csv.DictReader(open("partB/bench_log.csv")))
print(f"{'batch':>6}{'prompt':>8}{'reported':>10}{'recomputed':>12}")
for r in rows:
    total_tok = (int(r["prompt_len"]) + int(r["gen_len"])) * int(r["num_requests"])
    recomputed = total_tok / float(r["wall_clock_s"])
    print(f"{r['batch_size']:>6}{r['prompt_len']:>8}{r['reported_tok_s']:>10}{recomputed:>12.1f}")

print("\ngoodput for batch=24, prompt=3584 row (two independent methods):")
row = next(r for r in rows if r["batch_size"] == "24" and r["prompt_len"] == "3584")
m1 = int(row["num_requests"]) * int(row["gen_len"]) / float(row["wall_clock_s"])
m2 = int(row["batch_size"]) / (float(row["itl_ms_p50"]) / 1000)
print("method 1 (gen tokens / wall clock):", round(m1, 1), "tok/s")
print("method 2 (batch / itl_ms_p50):", round(m2, 1), "tok/s")
