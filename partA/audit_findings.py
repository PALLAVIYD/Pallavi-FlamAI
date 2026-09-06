import unicodedata
import regex
import tiktoken
from transformers import AutoTokenizer

gpt2_enc = tiktoken.get_encoding("gpt2")
muril_tok = AutoTokenizer.from_pretrained("google/muril-base-cased")
def muril_encode(s):
    return muril_tok.encode(s, add_special_tokens=False)

print("=== Bug 1: split(' ') vs split() (double-space -> phantom empty word) ===")
for fname in ["data/eng_sample.txt", "data/hin_sample.txt"]:
    with open(fname, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            line = unicodedata.normalize("NFC", line)
            bug, fix = line.split(" "), line.split()
            if len(bug) != len(fix):
                print(fname, repr(line))
                print("  split(' ') ->", len(bug), bug)
                print("  split()    ->", len(fix), fix)

print("\n=== Bug 2: lowercasing asymmetry -- effect on gpt2 vs muril token counts ===")
for fname in ["data/eng_sample.txt", "data/hin_sample.txt"]:
    lines = [l.strip() for l in open(fname, encoding="utf-8") if l.strip()]
    for name, encode in [("gpt2", gpt2_enc.encode), ("muril", muril_encode)]:
        for lower in (False, True):
            toks = sum(len(encode(l.lower() if lower else l)) for l in lines)
            print(fname, name, "lowercased" if lower else "original", "-> total tokens:", toks)

print("\n=== Bug 3: len() codepoints vs grapheme clusters (Hindi) ===")
total_cp, total_gr = 0, 0
for raw in open("data/hin_sample.txt", encoding="utf-8"):
    line = raw.strip()
    if not line:
        continue
    line = unicodedata.normalize("NFC", line)
    total_cp += len(line)
    total_gr += len(regex.findall(r"\X", line))
print("codepoints:", total_cp, "graphemes:", total_gr, "ratio:", round(total_cp / total_gr, 3))

print("\n=== Check: is `random` used anywhere besides the seed line? ===")
try:
    with open("partA/fertility_v0_original.py", encoding="utf-8") as fh:
        lines = fh.readlines()
    uses = [(i+1, l.rstrip()) for i, l in enumerate(lines) if "random." in l]
    if uses:
        for lineno, text in uses:
            print(f"  line {lineno}: {text}")
    else:
        print("(no other uses found -- dead import, harmless)")
except FileNotFoundError:
    print("(file not found -- skipping)")

