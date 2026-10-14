# experiment

[![Tests](https://github.com/antopaulogist/experiment/actions/workflows/tests.yml/badge.svg)](https://github.com/antopaulogist/experiment/actions/workflows/tests.yml)

When you ask your AI agent to make something better, this skill makes it prove
the change helps before it keeps it.

It works with AI coding agents such as Claude Code and Codex. You need to know
what you want improved and what a right answer looks like. You do not need to
know how to write tests or scoring code: the agent sets that up with you.

## An example

This is an invented example. On Saturday you are building a help chatbot for a
bike shop's website. Customers ask things like "Are you open on Sunday?" and
"How much is a puncture repair?", and the bot sometimes gets the hours or the
prices wrong. You open your agent in the project's folder and say:

> Use the experiment skill. I want my chatbot's instructions to answer
> questions about our opening hours and prices correctly, without getting
> worse at anything else. Try up to five ideas.

The agent asks what a right answer looks like and helps you collect examples:
a customer question and the answer it should get, such as "Are you open on
Sunday?" with "Yes, 10am to 4pm" (invented hours). It shuffles them into two
groups. It may read the first group while it works. The second group stays
hidden from it, and only the scoring uses it.

Then it measures your current chatbot on the hidden questions: say 9 of 30
answers come out wrong. It tries one idea at a time. After each try a script
checks the result. If fewer answers are wrong and nothing else broke, the
change stays. If not, the change is undone. When the five tries are used up,
it tells you where you started, where you ended up, which changes it kept, and
which ideas failed.

## Why the hidden examples matter

AI agents will usually tell you their change is an improvement. If the agent
also marks its own work, it can write instructions that answer the exact
questions it can see, word for word, without getting better at the questions
customers will really ask.

So in this skill the agent never decides what stays. A script scores every
change on examples the agent did not work on, and keeps the change only if the
score improves. Every try is written down, kept or not, so you can see what
was attempted.

## First steps

1. **Install it** by copying this folder into your agent's skills folder, so
   your agent can find it. Pick the line for your agent:

   ```bash
   # Codex, for all your projects:
   git clone https://github.com/antopaulogist/experiment ~/.agents/skills/experiment
   # Claude Code, for all your projects:
   git clone https://github.com/antopaulogist/experiment ~/.claude/skills/experiment
   # Claude Code, for one project (run from that project):
   git clone https://github.com/antopaulogist/experiment .claude/skills/experiment
   ```

   You need Git, Bash, Python 3.9 or newer, and your agent installed and
   logged in, on macOS or Linux. These paths come from the
   [Codex documentation](https://learn.chatgpt.com/docs/build-skills) and the
   [Claude Code documentation](https://code.claude.com/docs/en/skills). Other
   agents that read skills can use the same folder: copy it wherever that agent
   looks for skills, or point it at `SKILL.md`.

2. **Ask your agent in plain words**, and include three things: what to
   improve, what "better" means, and how many tries it may make. The agent needs
   the first two to build a fair score, and the number of tries caps what you
   spend. In Codex you can name the skill as `$experiment`, in Claude Code as
   `/experiment`, or just mention the experiment skill.

3. **Give it real examples with the right answers**, because the score is only
   as good as the examples. You need at least 20, because the split puts at
   least 10 in each group, and more is better: with few, a change can look
   better by luck. If you only have the inputs, the agent can
   draft the right answers with a model for you to check before the run starts.

4. **Check what it kept before you use it**, because a better score is not
   proof the change is right in every case. Read the kept change as you would
   any other edit to your project.

## What can go wrong

- **"Better" is hard to score.** When the goal is something like "make it read
  more naturally", a simple count can reward the wrong thing. Ask the agent to
  set up a blind comparison judge instead, and check its verdicts against your
  own on a few examples before the run.
- **Too few examples.** With a handful, a change can win by luck. Use more, and
  try kept changes on a fresh set of examples before you rely on them.
- **The starting measurement fails.** Then the setup is wrong, not your
  project. The agent should fix the setup before it tries any change.
- **A run is interrupted.** A stopped run can leave a half-finished record or
  an unfinished change in its working copy. Check both before you run again.

**Warning:** the hidden examples are kept in a separate folder, which only
hides them by layout. An agent that goes looking can still read them, and the
commands it runs have your account's permissions. Run experiments on a
throwaway copy of your project, with agents and commands you trust, so a
misbehaving try cannot damage your real files.

**Cost:** each try is one call to your agent, and a call can involve several
model turns. Scoring that uses a model, such as running your chatbot on the
hidden questions or asking a judge, adds calls of its own. Start with a few
tries and raise the limit once you know what a run costs you.

The skill has been run end to end with Codex. For Claude Code, the install
paths were checked against its documentation, but a live run was not tested for
this release.

## Reference

[REFERENCE.md](REFERENCE.md) covers setting up an experiment by hand, the
`lab split` command and its options, writing your own score and check scripts,
model judges, agent configuration and every setting. The command-line tool is
`scripts/lab`. The scripts can also run without Claude or Codex: use
`--agent command` with any command-line tool that accepts a prompt on standard
input (see [agent configuration](REFERENCE.md#agent-configuration)). The local
tests run with `python3 scripts/test_lab.py` and need no agent or login.

## Credit

Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch),
which uses the same loop of trying a change, measuring it and keeping or
discarding it, with a `program.md` for instructions and a `results.tsv` record.
This skill lets a script decide what to keep, hides the scoring examples from
the agent, adds checks that must still pass, judges for goals without a
built-in number, limits on tries and time, and a lessons file that carries over
between experiments.

## Licence

[MIT](LICENSE).
