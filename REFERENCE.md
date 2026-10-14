# Reference

See [README.md](README.md) for what the skill does and how to start. The command-line
tool is `scripts/lab`. Run the commands below from your own project folder, with
the skill path adjusted to where you installed it. Experiments are created in the
folder you run from, so never run them from inside your agent's skills folder.

## Installing by hand

Agents that can run commands, such as Claude Code and Codex, can install the
skill when you give them the repository link. To do it yourself, clone the repository into your agent's skills folder. Pick the line
for your agent:

```bash
# Codex, for all your projects:
git clone https://github.com/antopaulogist/experiment ~/.agents/skills/experiment
# Claude Code, for all your projects:
git clone https://github.com/antopaulogist/experiment ~/.claude/skills/experiment
# Claude Code, for one project (run from that project):
git clone https://github.com/antopaulogist/experiment .claude/skills/experiment
```

These paths come from the [Codex documentation](https://learn.chatgpt.com/docs/build-skills)
and the [Claude Code documentation](https://code.claude.com/docs/en/skills).
Other agents that read skills can use the same folder: copy it wherever that
agent looks for skills, or point it at `SKILL.md`. The folder follows the open
[Agent Skills format](https://agentskills.io/specification).

## Create your own experiment

Experiments default to `./lab` under the current directory, with records in
`./lab/experiments/NAME`. Override with `LAB_HOME` or the global `--lab-home`
flag, placed before the subcommand. Neither records nor working copies may
live inside the skill folder.

```bash
python3 experiment/scripts/lab new trial --workdir ./trial-work --agent codex
python3 experiment/scripts/lab split trial ./cases.jsonl
# Edit lab/experiments/trial/program.md and experiment.json; add your project
# files to trial-work, freeze development.jsonl, and commit on its lab-work branch.
python3 experiment/scripts/lab baseline trial
python3 experiment/scripts/lab run trial --tries 2 --patience 2 --minutes 10 --stale-minutes 5
python3 experiment/scripts/lab status trial
```

Alternatively, `new ... --repo PATH --base REF` creates a Git worktree on a
new `lab/NAME` branch. Existing workdirs must be dedicated and clean before
baseline/run, and may not be on main or master. The engine owns commits and
rollback in this disposable copy. Results and attempts stay outside it.

### Split your examples

When you have one pool of examples, call `split` after `new` and before
`baseline`. Keep the source pool outside the working copy so the agent does
not get the held-back answers alongside the files it edits. The input is a
UTF-8 JSONL file: one JSON object per line, with an `id` field. Blank lines are
ignored. An id must be a
nonempty string or an integer. Each id must be unique; `1` and `"1"` count as
the same id. Other fields, including your reference answers, are preserved.
For example, one line could be:

```json
{"id":"case-1","text":"at two pm","answer":"at 2pm"}
```

```bash
python3 experiment/scripts/lab split trial ./cases.jsonl
# Use a different repeatable shuffle and hold back 30 per cent:
python3 experiment/scripts/lab split trial ./cases.jsonl --seed 42 --held-back-share 0.3 --force
```

The default seed is `0` and the default held-back share is `0.5` (half).
The same input in the same order, seed and share gives the same files.
The held-back count is the share times the total, rounded down. The remaining
examples become development cases. Both groups must contain at least 10
examples, so the default needs at least 20. If either group is smaller, the
error gives both counts and asks you to add examples or change the share.
Ten is a lower limit for this tool, not evidence that a sample is representative.

The command prints the seed, counts and paths. It writes `development.jsonl`
in the configured working copy and `held-back.jsonl` in
`lab/experiments/NAME/` (or your chosen lab home). The experiment record folder
must be outside the working copy and the skill. Destination symlinks are
refused, and parent symlinks cannot bypass the path checks. An existing output
or split record requires `--force`, which replaces the split only before a
baseline exists. Once you have a baseline, use a new experiment for a new split.

`split.json` in the experiment record stores the seed, share, counts and
SHA-256 hashes, fingerprints of the source and both output files. Baseline
checks that the output files still match those fingerprints, copies the record
to `baseline-split.json`, and includes the seed, counts and output hashes in
`attempts/000-baseline.md`. A run also checks the files and recorded split
against the baseline before starting.

Commit `development.jsonl` in the working copy and add it to `frozen` in
`experiment.json`. Configure your scoring command to read the held-back file;
`split` does not change the scorer. If you already have development and
held-back files, keep that split and configure the scorer directly. Such
experiments do not get an automatic split record. Keep related examples
together when splitting by hand, so near-duplicates cannot occur in both groups.

## How to write score.sh and guard.sh

Set `metric_cmd` to `bash score.sh` and `guard_cmd` to `bash guard.sh`, or to
absolute external evaluator commands. Commands run with `workdir` as cwd.
`score.sh` must exit zero and print a single finite number on its final line;
diagnostics may precede it. `guard.sh` must exit zero only when every invariant
passes. Nonzero exit, timeout, or an invalid metric bins the change. For example:

```bash
#!/usr/bin/env bash
set -euo pipefail
python3 /path/to/frozen/evaluate.py  # score.sh: prints the number last
# guard.sh instead calls tests and returns their exit status
```

Freeze scripts, cases and references. Put held-back cases outside the editable
copy; only aggregate outputs should enter attempt records because those records
feed the next prompt. Use a separate development check inside the copy. Verify
that intentionally broken candidates fail the guards and worsen the number.
Scoring commands should be read-only and repeatable, with isolated build caches.

### Judge scripts

`teacher.py INPUTS GOLD --rubric RUBRIC` reads JSONL with `id` and `text` and
writes reference JSONL, resuming by id. `--field`, `--ids`, `--limit` and `--batch`
select inputs. Review references before freezing them.

`text_distance.py OUTPUTS GOLD` reports token edits per 100 reference words
(lower is better); missing outputs are penalised. Use `--ids` for a fixed split.

`pairwise.py SOURCE A_OUTPUTS B_OUTPUTS --rubric RUBRIC` compares matching JSONL
ids blindly in randomised order, then swaps every pair. Consistent preferences
count as wins; ties and order flips count half. Its final number is A's win
percentage (higher is better). `--details FILE` saves per-case judgments.
Neither missing nor malformed judge answers silently becomes a valid score.

Both model judges accept `--agent claude|codex|command` (default `claude`),
`--model`, `--effort`, `--timeout`, and `--command 'your-cli'`. Commands receive
prompts on stdin and return only the requested JSON lines on stdout. The judge
scripts must run from a writable experiment directory outside the skill.

### Agent configuration

`experiment.json` selects `agent`: `claude` (default if omitted), `codex`, or
`command`. Claude uses headless `claude --print`, the configured model and
effort, file-edit permission, no skills, and an empty MCP configuration generated
in a temporary directory. Codex uses `codex exec` with stdin, workspace-write
sandbox, no interactive approval, and the experiment's cwd. A `command` agent
requires a `command` shell string; it receives the prompt on stdin and runs in
that same cwd. Claude defaults to `sonnet`. For Codex, an omitted or empty
`model` leaves out `--model`, letting the CLI choose its built-in default
(user configuration is disabled). Set `model` explicitly to select a model
available to your account. Default effort is `medium`.

### Options and keep-or-bin rules

| Setting | Meaning |
| --- | --- |
| `name` | Experiment name, used in commit summaries. |
| `agent`, `command` | Agent adapter and, for `command`, the shell command to run. |
| `workdir` | Absolute path of the dedicated Git working copy. |
| `metric_cmd`, `guard_cmd` | Shell scoring and invariant checks; an empty guard skips it. |
| `direction` | `lower` or `higher` is better. |
| `epsilon` | A keep must improve by strictly more than this amount; default 0. |
| `editable` | Allowed relative file patterns; default all files. |
| `frozen` | Forbidden relative file patterns; overrides editable. |
| `model`, `effort` | Agent CLI settings, chosen for the selected provider. |
| `try_timeout` | Maximum seconds for one agent call; default 2400. |
| `metric_timeout` | Maximum seconds for the scoring command; default 1800. |
| `guard_timeout` | Maximum seconds for the guard command; default 1800. |
| `target` | Stop when the retained score reaches this number in the configured direction; null disables it. |
| `keep_simpler_within` | Also keep a change within this absolute score tolerance if editable files lose more lines than they gain; null disables it. |
| `on_keep_cmd` | Optional shell command after a committed keep, limited to 600 seconds; output and exit status are recorded. It must leave the copy clean. A hook failure does not reverse the verdict. |

`--tries` bounds attempts (default 10); `--patience` stops after consecutive bins
(default 5); `--minutes` bounds elapsed run time; `--stale-minutes` stops after
that many minutes without a keep. Time budgets are checked between attempts,
not mid-call; command timeouts bound individual operations. Zero disables the
time budgets. The retained score is the comparison point, including after a
permitted simplification that slightly worsens it.

Guards and frozen-file checks take precedence. Agent failures, no change and
metric failures are bins. Improvement beyond epsilon yields `keep`; a qualifying
deletion yields `keep: simpler`; otherwise `bin: no better`. Each try has a
Markdown record with hypothesis, full diff, outputs and verdict, plus a TSV row.
Kept changes are committed; binned changes are reset and untracked files removed.
Do not put unrelated work in the experiment copy.

## Cost

Each try is one agent CLI call; the engine does not retry it. A CLI call can
contain several model turns. Baseline costs only the configured guard/metric
commands. Model-based judges add calls of their own: teacher batches once per
batch, pairwise twice per batch. Provider pricing and your chosen model determine
cost. Use short budgets first.

## Limits

This needs a fast, honest number. It cannot establish product value, user trust,
meaning preservation or safety from an aggregate score alone. Small samples,
repeated held-back feedback, noisy judges and weak guards can produce misleading
wins. Audit retained changes on a fresh final split and with human review.
Frozen checks detect changes to files in the working copy; they do not sandbox
external files or stop a malicious proposer. Claude file permissions and Codex's
sandbox are useful boundaries, not a guarantee that evaluation data is secret.
Custom shell commands have your account's permissions. Use disposable copies
and trusted commands. Manual interruption or machine failure can leave an
incomplete record or dirty copy; inspect it and recover before resuming.
