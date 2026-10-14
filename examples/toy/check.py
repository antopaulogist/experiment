"""Evaluator lives outside the editable project; cwd is the project being scored."""
import json
import sys
from pathlib import Path
import cases
sys.path.insert(0, str(Path.cwd()))
import times

if sys.argv[1:] == ['guard']:
    broken = sum(times.normalise(text) != text for text in cases.KEEP)
    print(f'unchanged-phrase failures: {broken}')
    sys.exit(bool(broken))
examples = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
print(sum(times.normalise(case['text']) != case['answer'] for case in examples))
