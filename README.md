# experiment

[![Tests](https://github.com/antopaulogist/experiment/actions/workflows/tests.yml/badge.svg)](https://github.com/antopaulogist/experiment/actions/workflows/tests.yml)

An AI agent skill that tests whether a change improves a result you can
measure. It makes one change at a time, scores each change on examples the
agent does not see, keeps the changes that improve the score and undoes the
rest. Every attempt is recorded.

## Install

Ask your agent:

> Install the experiment skill from https://github.com/antopaulogist/experiment

To install it yourself, see
[Installing by hand](REFERENCE.md#installing-by-hand).

## Use

1. Ask your agent to use the experiment skill. Say what to improve, what counts
   as better, and the most tries it may make. For example:

   > Use the experiment skill to make my chatbot answer opening-hours questions
   > correctly. Try up to five changes.

2. The agent sets up the experiment with you. It needs:
   - examples with the correct answers, at least 20;
   - a way to score an answer;
   - any checks that must keep passing;
   - the try limit.

3. The agent splits the examples into two groups with `lab split`. It may read
   the first group. The second group, the held-back examples, is stored outside
   the folder it edits and is used only for scoring. Each group needs at least
   10 examples.

4. The agent scores the current version. This first score is the baseline.

5. The agent makes one change per try. After each try, a script runs the checks
   and scores the change on the held-back examples. The script keeps the change
   if the checks pass and the score improves. Otherwise it undoes the change.

6. When the tries run out, the agent reports the baseline, the final score, the
   changes it kept and the ideas that failed.

7. Review each kept change before you use it. A better score does not prove a
   change is correct in every case.

## Results

Each experiment is stored in `lab/experiments/NAME/`, under the folder the
agent ran it from:

| File | Contents |
|---|---|
| `results.tsv` | One row per try: time, score, best score so far, verdict and a short note |
| `attempts/` | One record per try: the idea, the full change, the output and the verdict |
| `split.json` | The split: seed, held-back share, counts and file fingerprints |
| `held-back.jsonl` | The held-back examples |

To see progress, ask your agent for the experiment's status, or run
`python3 <skill folder>/scripts/lab status NAME`.

## Cost

Each try is one call to your agent, and one call can include several model
turns. Scoring that uses a model, such as running a chatbot on the held-back
examples or a judge comparing answers, adds calls of its own. Start with a few
tries.

## Limits

- The goal needs a score that matches what you want. If "better" is hard to
  count, ask the agent to set up a blind comparison judge, and check its
  verdicts against your own on a few examples first.
- With few examples, a change can score better by luck. Use more examples, and
  test kept changes on new examples before relying on them.
- The held-back examples are separated by folder only. An agent that looks for
  them can still read them, and the commands it runs have your account's
  permissions. Run experiments on a copy of your project, with agents and
  commands you trust.
- If a run is interrupted, it can leave an unfinished record or change. Check
  both before running again.

The skill has been run end to end with Codex. For Claude Code, the install
paths were checked against its documentation; a live run was not tested for
this release.

## Reference

[REFERENCE.md](REFERENCE.md) covers installing by hand, setting up an
experiment without an agent, `lab split` options, writing score and check
scripts, model judges, agent configuration and all settings. The command-line
tool is `scripts/lab`. Run the tests with `python3 scripts/test_lab.py`; they
need no agent or sign-in.

## Credit

Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch).

## Licence

[MIT](LICENSE).
