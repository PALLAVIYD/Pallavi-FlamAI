#!/usr/bin/env python3
"""fertility_v2.py -- corrected tokenizer fertility benchmark, gpt2 + Indic-aware tokenizer."""
import argparse
import unicodedata
import regex
import tiktoken
from transformers import AutoTokenizer


def load_tokenizer(spec):
    if spec == "gpt2":
        enc = tiktoken.get_encoding("gpt2")
        return enc.encode
    elif spec.startswith("hf:"):
        tok = AutoTokenizer.from_pretrained(spec[3:])
        return lambda s: tok.encode(s, add_special_tokens=False)
    else:
        raise ValueError(f"unknown tokenizer spec: {spec}")


def read_lines(path):
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line:
                lines.append(unicodedata.normalize("NFC", line))
    return lines


def analyze(lines, encode, lowercase):
    per_word, per_grapheme, per_byte, per_sentence = [], [], [], []
    for line in lines:
        text = line.lower() if lowercase else line
        tokens = encode(text)
        n_tok = len(tokens)
        n_words = len(text.split())                        # fixed: no more split(" ")
        n_graphemes = len(regex.findall(r"\X", text))       # fixed: real character count
        n_bytes = len(text.encode("utf-8"))
        per_word.append(n_tok / n_words)
        per_grapheme.append(n_tok / n_graphemes)
        per_byte.append(n_tok / n_bytes)
        per_sentence.append(n_tok)                          # tokens per aligned sentence
    n = len(lines)
    return {
        "tok_per_word": sum(per_word) / n,
        "tok_per_grapheme": sum(per_grapheme) / n,
        "tok_per_byte": sum(per_byte) / n,
        "tok_per_sentence": sum(per_sentence) / n,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", action="append", required=True, metavar="LANG=PATH")
    ap.add_argument("--tokenizer", required=True, help="'gpt2' or 'hf:<repo_id>'")
    ap.add_argument("--lowercase", action="store_true", default=False,
                     help="apply .lower() before tokenizing (off by default -- see A2 finding)")
    args = ap.parse_args()

    encode = load_tokenizer(args.tokenizer)
    print(f"tokenizer: {args.tokenizer}   lowercase: {args.lowercase}")
    print(f"{'lang':<8}{'tok/word':>10}{'tok/grapheme':>14}{'tok/byte':>12}{'tok/sentence':>14}")
    print("-" * 58)

    results = {}
    for spec in args.corpus:
        lang, path = spec.split("=", 1)
        lines = read_lines(path)
        r = analyze(lines, encode, args.lowercase)
        results[lang] = r
        print(f"{lang:<8}{r['tok_per_word']:>10.2f}{r['tok_per_grapheme']:>14.3f}"
              f"{r['tok_per_byte']:>12.3f}{r['tok_per_sentence']:>14.2f}")

    langs = list(results)
    base = langs[0]
    print(f"\nratios vs {base}:")
    for lang in langs[1:]:
        for metric in results[base]:
            ratio = results[lang][metric] / results[base][metric]
            print(f"  {lang} {metric}: {ratio:.2f}x")


if __name__ == "__main__":
    main()
