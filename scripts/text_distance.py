#!/usr/bin/env python3
"""Score text outputs against reference ("gold") texts.

Both files are JSONL with an "id" and a text field. Prints a breakdown, and on
the LAST line one number: word edits needed per 100 gold words (lower is better).
Words are compared with case and punctuation kept, so a wrong capital or a
missing full stop counts; the breakdown separates those from word errors.

  text_distance.py OUTPUTS GOLD [--out-field text] [--gold-field text] [--ids FILE] [--json]
"""
import argparse, json, re, sys
from collections import Counter

TOKEN = re.compile(r"\w+(?:['’.:,-]\w+)*|[^\w\s]", re.UNICODE)
FILLERS = {"um", "uh", "er", "erm", "ah", "hmm", "mm"}


def tokens(text):
    return TOKEN.findall(text or "")


def align(a, b):
    """Minimum-edit alignment on tokens: list of (op, a_tok, b_tok)."""
    n, m = len(a), len(b)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
    ops, i, j = [], n, m
    while i or j:
        if i and j and d[i][j] == d[i - 1][j - 1] + (a[i - 1] != b[j - 1]):
            ops.append(("eq" if a[i - 1] == b[j - 1] else "sub", a[i - 1], b[j - 1])); i -= 1; j -= 1
        elif i and d[i][j] == d[i - 1][j] + 1:
            ops.append(("del", a[i - 1], None)); i -= 1
        else:
            ops.append(("ins", None, b[j - 1])); j -= 1
    return ops[::-1]


def kind(op, out_tok, gold_tok):
    """Why an edit is needed: what the output got wrong relative to gold."""
    t = out_tok if out_tok is not None else gold_tok
    if op == "sub" and out_tok.lower() == gold_tok.lower():
        return "capitals"
    if re.fullmatch(r"[^\w\s]", t or ""):
        return "punctuation"
    if any(ch.isdigit() for ch in (out_tok or "") + (gold_tok or "")):
        return "numbers"
    if op == "del":  # output has a word gold doesn't: a filler, or a stumble or restart left in
        return "filler left in" if (out_tok or "").lower() in FILLERS else "extra word left in"
    if op == "ins":  # gold has a word the output lost
        return "word lost"
    return "word changed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outputs"); ap.add_argument("gold")
    ap.add_argument("--out-field", default="text"); ap.add_argument("--gold-field", default="text")
    ap.add_argument("--ids", help="file of ids to score (one per line), e.g. a held-out split")
    ap.add_argument("--json", action="store_true", help="also print per-item results as JSON lines")
    a = ap.parse_args()
    gold = {}
    for line in open(a.gold):
        if line.strip():
            r = json.loads(line); gold[r["id"]] = r[a.gold_field]
    outs = {}
    for line in open(a.outputs):
        if line.strip():
            r = json.loads(line); outs[r["id"]] = r[a.out_field]
    ids = [l.strip() for l in open(a.ids)] if a.ids else sorted(gold)
    ids = [i for i in ids if i in gold]
    if not ids:
        ap.error("no reference cases selected")
    total_words, edits, kinds, missing = 0, 0, Counter(), 0
    for i in ids:
        g = tokens(gold[i]); o = tokens(outs.get(i, ""))
        if i not in outs:
            missing += 1
        total_words += max(1, sum(1 for t in g if re.match(r"\w", t)))
        for op, ot, gt in align(o, g):
            if op != "eq":
                edits += 1; kinds[kind(op, ot, gt)] += 1
        if a.json:
            print(json.dumps({"id": i, "edits": sum(1 for x in align(o, g) if x[0] != "eq")}))
    print(f"items {len(ids)} (missing outputs {missing}), gold words {total_words}, edits {edits}")
    for k, v in kinds.most_common():
        print(f"  {k}: {v} ({100 * v / total_words:.2f} per 100 words)")
    print(f"{100 * edits / max(total_words, 1):.3f}")


if __name__ == "__main__":
    main()
