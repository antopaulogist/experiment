#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 2 || ( $1 != claude && $1 != codex ) ]]; then
  echo 'usage: run.sh claude|codex DIR' >&2; exit 2
fi
agent=$1
tries=${TRIES:-1}
[[ $tries =~ ^[1-9][0-9]*$ ]] || { echo 'TRIES must be positive' >&2; exit 2; }
skill=$(cd "$(dirname "$0")/../.." && pwd -P)
# Refuse existing directories: every run must start fresh.
python3 - "$2" "$skill" <<'PY'
from pathlib import Path
import sys
p, skill = (Path(x).resolve() for x in sys.argv[1:])
if p == skill or skill in p.parents:
    sys.exit('DIR must be outside the skill')
p.mkdir(parents=True, exist_ok=False)
PY
dir=$(cd "$2" && pwd -P)
umask 077
mkdir -p "$dir/project" "$dir/evaluation" "$dir/runtime/tmp"
export TMPDIR="$dir/runtime/tmp"
export PYTHONDONTWRITEBYTECODE=1
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export CLAUDE_CODE_TMPDIR="$dir/runtime/tmp"
cleanup() {
  result=$?
  if [[ -f "$dir/lab/experiments/toy/results.tsv" ]]; then
    cat "$dir/lab/experiments/toy/results.tsv"
  fi
  exit "$result"
}
trap cleanup EXIT
cp "$skill/examples/toy/times.py" "$dir/project/times.py"
cp "$skill/examples/toy/cases.py" "$dir/evaluation/cases.py"
cp "$skill/examples/toy/check.py" "$dir/evaluation/check.py"
cat > "$dir/project/README.md" <<'EOF'
Improve normalise(text) in times.py to format spoken times without changing other words.
Read development.jsonl for examples and their reference answers.
Leave unrelated phrases unchanged. Make one general rule per try. Do not inspect
files outside this project, use other agents, or run background commands.
EOF
python3 "$skill/scripts/lab" --lab-home "$dir/lab" new toy --workdir "$dir/project" --agent "$agent"
python3 "$dir/evaluation/cases.py" > "$dir/evaluation/all-cases.jsonl"
python3 "$skill/scripts/lab" --lab-home "$dir/lab" split toy "$dir/evaluation/all-cases.jsonl"
git -C "$dir/project" add development.jsonl
git -C "$dir/project" -c user.name=lab -c user.email= commit -q -m 'lab: record development cases'
python3 - "$dir/lab/experiments/toy" "$dir" <<'PY'
import json, os, shlex, sys
from pathlib import Path
exp, root = map(Path, sys.argv[1:])
cfg = json.loads((exp/'experiment.json').read_text())
check = 'python3 ' + shlex.quote(str(root/'evaluation/check.py'))
cfg.update(metric_cmd=check+' '+shlex.quote(str(exp/'held-back.jsonl')),
           guard_cmd=check+' guard', editable=['times.py'],
           frozen=['README.md', 'development.jsonl'], try_timeout=180, metric_timeout=30, guard_timeout=30)
if os.environ.get('MODEL'):
    cfg['model'] = os.environ['MODEL']
(exp/'experiment.json').write_text(json.dumps(cfg, indent=2)+'\n')
(exp/'program.md').write_text('''# Spoken times
Make spoken times easier to read, preserving meaning and unrelated phrases.
The number is failing held-back examples (lower is better). Guard phrases must
remain unchanged. Only times.py may change. Read development.jsonl for
examples. Add one general conversion rule. Do not inspect evaluation files.
Stop after the configured number of tries. Write ATTEMPT.md with your hypothesis.
''')
PY
python3 "$skill/scripts/lab" --lab-home "$dir/lab" baseline toy
python3 "$skill/scripts/lab" --lab-home "$dir/lab" run toy --tries "$tries" --patience "$tries"
python3 - "$dir/lab/experiments/toy/results.tsv" "$tries" <<'PY'
import csv, sys
from pathlib import Path
p = Path(sys.argv[1])
rows = list(csv.DictReader(p.open(), delimiter='\t'))
assert len(rows) == int(sys.argv[2])+1, 'not every try was recorded'
assert rows[0]['verdict'] == 'baseline', 'baseline failed'
for n, row in enumerate(rows[1:], 1):
    assert row['verdict'] in ('keep', 'keep: simpler') or row['verdict'].startswith('bin: ')
    assert (p.parent/'attempts'/f'{n:03d}.md').is_file()
PY
