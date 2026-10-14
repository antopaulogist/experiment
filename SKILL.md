---
name: experiment
description: Test whether a proposed change improves a measurable outcome using a bounded keep-or-bin experiment, independent scoring, guards, and a record of every attempt.
---

# Find out whether B is better than A

Own an honest answer at an agreed cost. Read [README.md](README.md) for commands
and [REFERENCE.md](REFERENCE.md) for configuration. Read [lessons.md](lessons.md)
before choosing a hypothesis.

Before a loop starts, establish:

- A goal stated without prescribing the solution.
- One defensible number, its direction, and which errors it can hide.
- Representative development cases and separate held-back evaluation cases.
- Guards for behaviour that must survive, even if the score improves.
- A target, attempt count, plateau, or time budget authorised by the user.

Build and check the judge first. For text, use [scripts/teacher.py](scripts/teacher.py)
to generate references and [scripts/text_distance.py](scripts/text_distance.py)
to score outputs, or [scripts/pairwise.py](scripts/pairwise.py) for blind,
order-swapped comparisons. Check a known-good and a known-bad example against
human judgments and record agreement before trusting that judge.

Create an experiment with [scripts/lab](scripts/lab) and a dedicated disposable
working copy outside this skill. Fill the contract from
[template/program.md](template/program.md), freeze the evaluator, and configure
the selected agent. When the user has one pool of examples, use
`lab split NAME CASES` before running the agent. It puts development examples
in the working copy and held-back examples in the experiment record folder.
Keep the full source pool outside the working copy too. Keep the user's own
split only when they already have one. See [splitting examples](REFERENCE.md#split-your-examples)
for the JSONL format, seed, share and minimum group size. Commit the development
file and freeze it before baseline. Point the scoring command at the held-back
file; `split` does not configure the scorer for you.

Keep held-back cases outside the agent's working copy;
do not include case-level answers in prompts or attempt feedback. This is an
honest experimental protocol, not an adversarial security boundary.

Run `baseline` first. If it fails, fix the setup before attempting improvements.
Run a bounded `run`: one hypothesis and one change per try. The script runs
guards and the held-back metric, records the diff and outputs, and decides
keep or bin. Never manually label an attempt successful or silently change the
judge to rescue a failed attempt. Changing the judge requires a new baseline
in a new experiment. Use `status` to inspect progress.

Finish with the baseline and final numbers, kept changes, useful failed ideas,
and remaining human checks. Store experiment-specific lessons beside its
contract; propose only general lessons for the shared lessons file. A kept
change still needs the project's ordinary review before it is shipped.
