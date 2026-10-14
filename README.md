# experiment

[![Tests](https://github.com/antopaulogist/experiment/actions/workflows/tests.yml/badge.svg)](https://github.com/antopaulogist/experiment/actions/workflows/tests.yml)

It's a tool that checks whether a change made by an AI actually improves
something. You give it three things: the thing to improve (a program, some
instructions, a piece of writing), a set of examples with the right answers,
and a way to score an answer, such as counting the differences from the right
one. When you ask your AI agent to run an experiment, the skill has it use
`lab split` to shuffle the examples into two groups before trying changes.
The AI can see the first group and try ideas on it. The second group, the
held-back cases, goes in a folder outside the one it edits. If you already have
a split, you can keep it.

Then it runs in a loop. The AI makes one small change. The tool scores the
result on the held-back group, keeps the change if the score improved, and
undoes it if not. Every attempt is logged, kept or not. The held-back group
matters because an AI scored on examples it can see can learn those examples
instead of getting better at the task. Keeping files separate is not a guarantee
that an agent cannot read them.

For example, you could improve a text clean-up function that turns "at two pm"
into "at 2pm". Give it reference answers and check that it leaves unrelated
words alone. Try it with the [two-command toy](#try-the-toy) below.

Requirements: Python 3.9+ (standard library only), Bash, Git and a logged-in agent command-line tool on macOS or Linux.

## Install for your agent

This repository is the skill folder. It follows the open
[Agent Skills format](https://agentskills.io/specification), with `name` and
`description` in `SKILL.md`. Clone it directly into your agent's skills folder.
Choose one installation:

```bash
# Codex, for all your projects:
git clone https://github.com/antopaulogist/experiment ~/.agents/skills/experiment
# Claude Code, for all your projects:
git clone https://github.com/antopaulogist/experiment ~/.claude/skills/experiment
# Claude Code, for one project (run from that project):
git clone https://github.com/antopaulogist/experiment .claude/skills/experiment
```

These paths follow the [Codex documentation](https://learn.chatgpt.com/docs/build-skills)
and [Claude Code documentation](https://code.claude.com/docs/en/skills).
Ask Codex to use `$experiment`, or Claude Code to use `/experiment`.
For other agents, copy the folder wherever that agent reads skills, or point it
at `SKILL.md`. The scripts also run on their own: use `--agent command` with any
CLI that accepts a prompt on standard input, and set `command` in
`experiment.json`. See the [reference](REFERENCE.md#agent-configuration).
The command-line tool is `scripts/lab`.

## Try the toy

With the Codex installation above and Codex already logged in, run these two
commands from any folder. Choose a new output folder if `~/experiment-toy`
already exists. The output must be outside the installed skill.

```bash
bash ~/.agents/skills/experiment/examples/toy/run.sh codex ~/experiment-toy
python3 ~/.agents/skills/experiment/scripts/lab --lab-home ~/experiment-toy/lab status toy
```

The runner creates a disposable copy of the toy and calls `lab split` on
24 examples. The default seed, 0, is a fixed number that makes the shuffle
repeatable. It writes 12 development examples to `project/development.jsonl`
and 12 held-back examples to `lab/experiments/toy/held-back.jsonl` under your
output folder. It prints both paths and records the split. For your own pool,
use `lab split NAME CASES`; the [reference](REFERENCE.md#split-your-examples)
explains the file format and options.

The runner scores the starting version (the baseline), then asks Codex for
one change. It allows three minutes for the agent call, which may incur provider
charges. Results vary. Here is `results.tsv` from a real run with Codex CLI 0.154.0:

```text
n	at	score	best	verdict	note
0	2026-10-14T19:02:52	12.0	12.0	baseline
1	2026-10-14T19:03:38	9.0	9.0	keep	Convert spelled-out hours followed by am or pm into compact numeric times.
```

The status command from that same run printed:

```text
toy: baseline 12.0 -> best 9.0 (lower is better); 1 attempts, 1 kept
  #0 baseline               12.0
  #1 keep                   9.0  Convert spelled-out hours followed by am or pm into compact numeric times.
```

The score counts failing examples, so 9 is better than 12. The change was kept.
A completed run can also reject a change; check the attempt record if it reports
an agent failure. Codex was tested end to end for this example. Claude Code's
installation paths were checked against its documentation; its live agent run
was not tested for this release.

## How it decides

The script runs checks for behaviour that must stay true, called guards, then
scores the change. It keeps a change only when those checks pass, the agent
changes only allowed files, and the score improves by more than the configured
minimum. You can also allow changes that remove code without worsening the
score beyond a chosen tolerance. It commits kept changes and undoes rejected
ones in a dedicated working copy, a disposable folder containing the files the
agent edits. Every attempt goes into `results.tsv` and a separate record.

Read [REFERENCE.md](REFERENCE.md) to set up your own experiment, configure
agents and scoring, use model judges when there is no direct numerical measure,
and set budgets. It also covers costs and limits, including why repeated use
of the same held-back examples can give misleading results. Run the local
checks from this repository with `python3 scripts/test_lab.py`; they need no
agent CLI or login.

## Credit

Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch):
the same core loop of proposing, measuring, keeping or discarding, with
`program.md` for instructions and `results.tsv` for the record. Here a script
runs the checks and decides what to keep. The workflow adds held-back cases
outside the agent's folder, guards, model judges when there is no direct
number, attempt and time budgets, and a lessons file.

## Licence

[MIT](LICENSE).
