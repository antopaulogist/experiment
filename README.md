# experiment

[![Tests](https://github.com/antopaulogist/experiment/actions/workflows/tests.yml/badge.svg)](https://github.com/antopaulogist/experiment/actions/workflows/tests.yml)

Find out whether a change your AI agent makes is actually an improvement.

## What it does

You give it three things:

- the thing to improve, such as a program, a prompt or a piece of writing;
- examples with the right answers;
- a way to score an answer, such as counting how many examples it gets wrong.

Then it works in a loop. The agent makes one small change. A script scores the
result, keeps the change if the score improved and undoes it if not. The agent
never scores its own work. Every attempt is logged, kept or not.

The score comes from examples the agent never works on. When you ask your agent
to run an experiment, the skill has it run `lab split` first, which shuffles
your examples into two groups. The agent can read the first group and try ideas
on it. The second group, the held-back cases, goes in a folder outside the one
it edits, and only the scoring uses it. An agent scored on examples it can see
tends to learn those examples instead of getting better at the task. Keeping
the files apart protects them by layout only: an agent that goes looking can
still read them. If you already have your own split, you can keep it.

A typical use is a text clean-up function that should turn "at two pm" into
"at 2pm". You give it reference answers to score against and a check that it
leaves unrelated words alone. The [two-command toy](#try-the-toy) below does
exactly this.

Requirements: Python 3.9+ (standard library only), Bash, Git and a logged-in
agent command-line tool on macOS or Linux.

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

With the Codex installation above and Codex logged in, run these two commands
from any folder. Pick an output folder that does not exist yet and is not inside
the installed skill.

```bash
bash ~/.agents/skills/experiment/examples/toy/run.sh codex ~/experiment-toy
python3 ~/.agents/skills/experiment/scripts/lab --lab-home ~/experiment-toy/lab status toy
```

What happens: the runner makes a disposable copy of a small project with 24
examples and splits them with `lab split`. It writes 12 development examples to
`project/development.jsonl` and 12 held-back examples to
`lab/experiments/toy/held-back.jsonl` under your output folder. It scores the
starting version (the baseline), then asks Codex for one change. The agent call
is allowed three minutes and may cost you provider usage. Results vary between
runs.

From a real run with Codex CLI 0.154.0, `results.tsv` read:

```text
n	at	score	best	verdict	note
0	2026-10-14T19:02:52	12.0	12.0	baseline
1	2026-10-14T19:03:38	9.0	9.0	keep	Convert spelled-out hours followed by am or pm into compact numeric times.
```

and the status command printed:

```text
toy: baseline 12.0 -> best 9.0 (lower is better); 1 attempts, 1 kept
  #0 baseline               12.0
  #1 keep                   9.0  Convert spelled-out hours followed by am or pm into compact numeric times.
```

The score counts failing examples, so lower is better. One change took it from
12 to 9, and the script kept it. A run can also end with the change rejected.
If it reports an agent failure, check the attempt record.

The split uses seed 0 by default, so the same examples always split the same
way. For your own pool of examples, run `lab split NAME CASES`. The
[reference](REFERENCE.md#split-your-examples) explains the file format, the seed
and the other options.

This example was tested end to end with Codex. For Claude Code, the install
paths were checked against its documentation, but a live run was not tested for
this release.

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
