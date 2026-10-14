#!/usr/bin/env python3
"""A blind A-or-B judge. For each id, a model sees the source and two outputs in a
random order (never which system made which) and picks the better one against a
rubric, or a tie. Every pair is judged twice with the order swapped; a pick that
flips with the order counts as a tie, which removes the judge's position bias.

Prints a breakdown, and on the LAST line the win rate of system A (ties count
half), as a percentage.

  pairwise.py SOURCE A_OUTPUTS B_OUTPUTS --rubric RUBRIC.md
              [--agent claude|codex|command] [--source-field text] [--field text] [--batch 20] [--ids FILE] [--details OUT.jsonl]
"""
import argparse, json, random, sys
sys.dont_write_bytecode = True
from agents import judge_options, judge_answer


def load(path, field):
    out = {}
    for line in open(path):
        if line.strip():
            r = json.loads(line); out[r["id"]] = r.get(field, "")
    return out


def judge(rubric, triples, args):
    prompt = (f"{rubric}\n\nFor each item, compare output X and output Y against the source and the rubric. "
              'Answer with exactly one JSON line per item: {"id": ..., "pick": "X" | "Y" | "tie"}. Nothing else.\n\n'
              + "\n".join(json.dumps({"id": i, "source": s, "X": x, "Y": y}, ensure_ascii=False) for i, s, x, y in triples))
    text = judge_answer(prompt, args)
    picks = {}
    for line in text.splitlines():
        line = line.strip().strip(",")
        if line.startswith("{"):
            try:
                r = json.loads(line); picks[r["id"]] = r.get("pick")
            except json.JSONDecodeError:
                pass
    if any(picks.get(i) not in ("X", "Y", "tie") for i, *_ in triples):
        raise SystemExit("judge returned missing or invalid picks")
    return picks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source"); ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("--rubric", required=True)
    ap.add_argument("--source-field", default="text"); ap.add_argument("--field", default="text")
    ap.add_argument("--batch", type=int, default=20); ap.add_argument("--ids")
    judge_options(ap)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--details", help="write each item's two picks and verdict here, one JSON line per item")
    a = ap.parse_args()
    rubric = open(a.rubric).read()
    src, A, B = load(a.source, a.source_field), load(a.a, a.field), load(a.b, a.field)
    ids = [l.strip() for l in open(a.ids)] if a.ids else sorted(src)
    if any(i not in A or i not in B or i not in src for i in ids):
        ap.error("every selected source id needs both candidate outputs")
    if not ids or a.batch < 1:
        ap.error("need at least one matching case and a positive batch size")
    rng = random.Random(a.seed)
    wins = ties = losses = 0
    details = []
    for s in range(0, len(ids), a.batch):
        chunk = ids[s:s + a.batch]
        first = {i: rng.random() < 0.5 for i in chunk}  # True: A shown as X
        p1 = judge(rubric, [(i, src[i], A[i] if first[i] else B[i], B[i] if first[i] else A[i]) for i in chunk], a)
        p2 = judge(rubric, [(i, src[i], B[i] if first[i] else A[i], A[i] if first[i] else B[i]) for i in chunk], a)
        for i in chunk:
            def who(pick, a_is_x):
                if pick == "tie" or pick is None:
                    return "tie"
                return "A" if (pick == "X") == a_is_x else "B"
            r1, r2 = who(p1.get(i), first[i]), who(p2.get(i), not first[i])
            details.append({"id": i, "first_order": r1, "swapped_order": r2,
                            "verdict": r1 if r1 == r2 and r1 != "tie" else "tie"})
            if r1 == r2 == "A":
                wins += 1
            elif r1 == r2 == "B":
                losses += 1
            else:
                ties += 1
    n = wins + ties + losses
    if a.details:
        with open(a.details, "w") as fh:
            fh.write("".join(json.dumps(d) + "\n" for d in details))
    print(f"pairs {n}: A wins {wins}, B wins {losses}, ties or flips {ties}")
    print(f"{100 * (wins + 0.5 * ties) / max(n, 1):.1f}")


if __name__ == "__main__":
    main()
