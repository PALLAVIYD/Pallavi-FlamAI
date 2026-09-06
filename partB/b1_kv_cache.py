layers, kv_heads, head_dim, dtype_bytes = 28, 8, 128, 2
bytes_per_token = 2 * layers * kv_heads * head_dim * dtype_bytes
print("bytes per token:", bytes_per_token)

gpu_mem_gb, util = 24, 0.92
weight_params_b, weight_dtype_bytes = 4.2, 2
overhead_gb = 1.6
usable_gb = gpu_mem_gb * util
weights_gb = weight_params_b * 1e9 * weight_dtype_bytes / 1e9
kv_budget_gb = usable_gb - weights_gb - overhead_gb
seq_len = 4096
bytes_per_seq = bytes_per_token * seq_len
max_concurrent = kv_budget_gb * 1e9 / bytes_per_seq
print("usable GB:", usable_gb, "weights GB:", weights_gb, "KV budget GB:", kv_budget_gb)
print("bytes per 4096-token sequence:", bytes_per_seq)
print("max concurrent sequences:", max_concurrent)
