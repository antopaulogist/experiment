# experiment

[![Tests](https://github.com/antopaulogist/experiment/actions/workflows/tests.yml/badge.svg)](https://github.com/antopaulogist/experiment/actions/workflows/tests.yml)

## What is it?

A free skill for AI agents such as Claude Code. Point it at something you want
to improve, and it works out how.

## What problem does it solve?

You know something could work better, but not which change would do it.
Guessing takes time, and a change that looks better on a few tries can be worse
overall. This skill lets the agent find the changes itself. It comes up with
ideas, tests each one fairly, keeps what makes the result better and drops what
doesn't.

## How can I use it?

Tell your agent:

> Install the experiment skill from github.com/antopaulogist/experiment.

Then tell it what to improve. For example:

> Improve our website chatbot's rules so it gets fewer customer questions wrong.

Give it some real questions with the right answers. It tries adding, changing
and removing rules one at a time, keeps each change that cuts the wrong
answers, and drops the rest.

## Install

An AI agent is an AI tool that can read and change files on your computer and
run commands there. Claude Code and Codex are agents. A skill is a folder of
instructions and small programs that teaches an agent a new task. The agent
reads it when you ask for that task.

To install this skill, send your agent the install line under
[How can I use it?](#how-can-i-use-it). The agent copies this repository into
the folder where it keeps its skills. If the agent does not find the skill
afterwards, start a new session with it.

To install it yourself with terminal commands, see
[Installing by hand](REFERENCE.md#installing-by-hand). That section also lists
the software the skill needs and the systems it is tested on.

## Use

1. Ask your agent to use the experiment skill. Say what to improve, what counts
   as better, and the most tries it may make. A try is one change, tested and
   then kept or undone. For example:

   > Use the experiment skill to make my chatbot answer opening-hours questions
   > correctly. Try up to five changes.

2. The agent sets up the experiment with you. It needs:
   - at least 20 examples with the correct answers, because every change is
     tested against them;
   - a way to score an answer: a command that runs your project on the
     examples and prints one number, such as how many answers were wrong. The
     agent can write this with you;
   - any checks that must keep passing: tests that show a change has not
     broken something else;
   - the try limit, which caps the cost (see [Cost](#cost)).

3. The agent splits the examples into two groups with the skill's `lab split`
   command. It may read the first group to get ideas. The second group, the
   held-back examples, is stored outside the folder it edits and is used only
   for scoring. This stops a change from being fitted to the exact examples it
   is scored on, which would make it look better than it is. Each group needs
   at least 10 examples.

4. The agent scores the current version before it changes anything. This first
   score is called the baseline. A change is kept only if it beats the best
   score so far, starting with the baseline.

5. The agent makes one change per try, so each score shows the effect of that
   one change. After each try, a script that comes with the skill runs the
   checks and scores the change on the held-back examples. The script keeps the
   change if the checks pass and the score improves. Otherwise it undoes the
   change. The agent does not decide which changes are kept.

6. When the run ends, the agent reports the baseline, the final score, the
   changes it kept and the ideas that failed.

7. Review each kept change before you use it. A better score shows that the
   change helped on the held-back examples. It does not prove the change is
   correct in every case.

## Results

The skill keeps a record of each experiment in a folder named
`lab/experiments/NAME/`, where NAME is the experiment's name. The `lab` folder
is created inside the folder the agent ran the experiment from. The experiment
folder holds:

| File | Contents |
|---|---|
| `results.tsv` | A table with one row per try: time, score, best score so far, verdict and a short note. It opens in a spreadsheet. |
| `attempts/` | One record per try: the idea, the full change, the output and the verdict |
| `split.json` | How the examples were split: the seed that fixed the shuffle, the share held back, the number in each group, and a fingerprint of each file so a later edit to them can be detected |
| `held-back.jsonl` | The held-back examples |

The kept changes themselves are in the experiment's working copy, a separate
copy of your files that the experiment edits. Each kept change is saved there
as its own Git commit, a saved version of the files. Ask your agent to show you
each kept change.

To see progress, ask your agent for the experiment's status. In a terminal, the
same information comes from `python3 <skill folder>/scripts/lab status NAME`,
where `<skill folder>` is the folder the skill was installed in.

## Cost

Each try starts your agent once, and the agent can send several requests to its
AI model during that try. These requests count against your agent's normal plan
or billing. Scoring that uses an AI model, such as running a chatbot on the
held-back examples or a judge comparing answers, adds requests of its own.
Start with a few tries so you can see the cost before a longer run.

## Limits

- The skill improves the score it is given, so the score has to match what you
  want. If "better" is hard to count, ask the agent to set up a blind
  comparison judge: an AI model that compares two answers without knowing which
  version wrote each one. Check its verdicts against your own on a few examples
  before you rely on it.
- With few examples, a change can score better by luck. Use more examples, and
  test kept changes on new examples before relying on them.
- The held-back examples are kept apart only by being in a different folder.
  They are not locked. An agent that looks for them can still read them. The
  commands the agent runs can do anything your user account can do. Run
  experiments on a copy of your project, with agents and commands you trust,
  so a mistake cannot damage the original.
- If a run is interrupted, for example because the agent is stopped or the
  computer shuts down, it can leave an unfinished record or a half-made change.
  Ask your agent to check both before running again.

The skill has been tested from start to finish with Codex. For Claude Code, the
install folders were checked against Claude Code's documentation, but a full
run was not tested for this release.

## Reference

[REFERENCE.md](REFERENCE.md) is for readers who use a terminal or want to
change settings. It covers installing by hand, setting up an experiment without
an agent, the options for `lab split`, writing the score and check scripts
(`score.sh` and `guard.sh`), judges that use an AI model to score answers,
agent settings and every setting in the experiment file. The skill's
command-line tool is `scripts/lab`. To test the skill itself, run
`python3 scripts/test_lab.py` from the skill folder. The tests need no agent
and no sign-in.

## Credit

Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch).

## Licence

Free to use, change and share under the [MIT licence](LICENSE).
