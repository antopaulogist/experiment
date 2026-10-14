#!/usr/bin/env python3
"""The teacher: a frontier model writes the reference ("gold") answer for each input.

Reads JSONL inputs, sends them in batches with a rubric to the selected agent CLI, and
appends {"id", "text"} lines to the gold file. Resumable: ids already in the gold
file are skipped. The rubric is a plain text file that says what ideal looks like.

  teacher.py INPUTS GOLD --rubric RUBRIC.md [--field text] [--batch 40]
             [--agent claude|codex|command] [--model MODEL] [--effort high] [--limit N] [--ids FILE]
"""
import argparse, json, subprocess, sys, time

sys.dont_write_bytecode = True
from agents import judge_options, judge_answer


def parse(out):
    got = {}
    for line in out.splitlines():
        line = line.strip().strip(",")
        if line.startswith("{") and '"id"' in line:
            try:
                r = json.loads(line)
                if "id" in r and "text" in r:
                    got[r["id"]] = r["text"]
            except json.JSONDecodeError:
                pass
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs"); ap.add_argument("gold"); ap.add_argument("--rubric", required=True)
    ap.add_argument("--field", default="text"); ap.add_argument("--batch", type=int, default=40)
    judge_options(ap)
    ap.add_argument("--limit", type=int, default=0); ap.add_argument("--ids")
    a = ap.parse_args()
    if a.batch < 1:
        ap.error("batch must be positive")
    rubric = open(a.rubric).read()
    done = set()
    try:
        done = {json.loads(l)["id"] for l in open(a.gold) if l.strip()}
    except FileNotFoundError:
        pass
    want = {l.strip() for l in open(a.ids)} if a.ids else None
    items = []
    for line in open(a.inputs):
        if not line.strip():
            continue
        r = json.loads(line)
        if r["id"] in done or (want is not None and r["id"] not in want) or not (r.get(a.field) or "").strip():
            continue
        items.append({"id": r["id"], "text": r[a.field]})
    if a.limit:
        items = items[: a.limit]
    print(f"{len(items)} to do, {len(done)} already done", flush=True)
    for start in range(0, len(items), a.batch):
        chunk = items[start:start + a.batch]
        prompt = (f"{rubric}\n\nFor each input line below, output exactly one JSON line "
                  '{"id": ..., "text": ...} with the ideal version, in the same order, and nothing else.\n\n'
                  + "\n".join(json.dumps(c, ensure_ascii=False) for c in chunk))
        got = parse(judge_answer(prompt, a))
        if any(c["id"] not in got or not isinstance(got[c["id"]], str) for c in chunk):
            raise SystemExit("judge returned incomplete or malformed references; rerun to resume")
        with open(a.gold, "a") as f:
            for c in chunk:
                if c["id"] in got:
                    f.write(json.dumps({"id": c["id"], "text": got[c["id"]]}, ensure_ascii=False) + "\n")
        print(f"batch {start // a.batch + 1}: {len(got)}/{len(chunk)}", flush=True)


if __name__ == "__main__":
    main()
