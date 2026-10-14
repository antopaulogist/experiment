"""Deterministic regression checks; run from inside or outside the skill."""
import csv
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
loader = importlib.machinery.SourceFileLoader('lab', str(SCRIPTS/'lab'))
spec = importlib.util.spec_from_loader(loader.name, loader)
lab = importlib.util.module_from_spec(spec)
loader.exec_module(lab)
import agents


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.lab-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.wd = self.root/'work'
        self.wd.mkdir()
        (self.wd/'value').write_text('10\nextra\n')
        (self.wd/'frozen file').write_text('fixed\n')
        self.run_lab('new', 'trial', '--workdir', str(self.wd), '--agent', 'command')
        self.exp = self.root/'lab/experiments/trial'
        self.cfg = json.loads((self.exp/'experiment.json').read_text())
        self.cfg.update(metric_cmd='head -n 1 value', guard_cmd='test -s value',
                        editable=['value', 'new'], frozen=['frozen*'],
                        command="printf '9\\nextra\\n' > value; printf hypothesis > ATTEMPT.md")
        self.save()
        self.run_lab('baseline', 'trial')

    def save(self):
        (self.exp/'experiment.json').write_text(json.dumps(self.cfg))

    def run_lab(self, *args, success=True):
        p = subprocess.run([sys.executable, str(SCRIPTS/'lab'), '--lab-home',
                            str(self.root/'lab'), *args], capture_output=True, text=True)
        if success:
            self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
        return p

    def attempt(self, expected, **changes):
        self.cfg.update(changes)
        self.save()
        self.run_lab('run', 'trial', '--tries', '1')
        rows = list(csv.DictReader((self.exp/'results.tsv').read_text().splitlines(), delimiter='\t'))
        self.assertEqual(rows[-1]['verdict'], expected)
        record = (self.exp/'attempts'/f"{len(rows)-1:03d}.md").read_text()
        self.assertIn('## Diff', record)
        clean = subprocess.check_output(['git', 'status', '--porcelain'], cwd=self.wd, text=True)
        self.assertEqual(clean, '')
        return record

    def test_keep_and_hook(self):
        record = self.attempt('keep', on_keep_cmd='printf hook-output')
        self.assertIn('hook-output', record)
        self.assertEqual((self.wd/'value').read_text(), '9\nextra\n')

    def test_epsilon_boundary_and_rollback(self):
        self.attempt('bin: no better', epsilon=1)
        self.assertEqual((self.wd/'value').read_text(), '10\nextra\n')

    def test_guard_failure(self):
        self.attempt('bin: guards failed', guard_cmd='exit 1')

    def test_invalid_and_failed_metrics(self):
        for command in ('echo nan', 'echo infinity', 'echo "score 2"', 'exit 1'):
            self.attempt('bin: metric failed', metric_cmd=command)

    def test_frozen_staged_file(self):
        self.attempt('bin: touched frozen file', command="echo changed > 'frozen file'; git add -A")
        self.assertEqual((self.wd/'frozen file').read_text(), 'fixed\n')

    def test_new_file_in_diff(self):
        record = self.attempt('keep', command="echo 9 > value; echo content > new")
        self.assertIn('+content', record)
        self.assertIn('New files: new', record)

    def test_staged_new_file_in_record(self):
        record = self.attempt('keep', command='echo 9 > value; echo content > new; git add new')
        self.assertIn('New files: new', record)

    def test_simpler_and_higher(self):
        self.attempt('keep: simpler', command='echo 10 > value', keep_simpler_within=0)
        self.attempt('keep', direction='higher', command='echo 11 > value')

    def test_agent_failure(self):
        self.attempt('bin: agent failed (7)', command='echo 1 > value; exit 7')

    def test_no_change_and_patience(self):
        self.cfg['command'] = 'true'
        self.save()
        self.run_lab('run', 'trial', '--tries', '3', '--patience', '1')
        self.assertEqual(len((self.exp/'results.tsv').read_text().splitlines()), 3)

    def test_target_stops(self):
        self.cfg['target'] = 10
        self.save()
        self.run_lab('run', 'trial', '--tries', '2')
        self.assertEqual(len((self.exp/'results.tsv').read_text().splitlines()), 2)

    def test_timeout(self):
        self.attempt('bin: agent failed (124)', command=f'{shlex.quote(sys.executable)} -c "import time; time.sleep(2)"', try_timeout=0.05)

    def test_skill_directory_rejected(self):
        for path in (SCRIPTS.parent, SCRIPTS.parent/'nested'/'work'):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'outside the skill folder'):
                lab.outside_skill(path)
        p = subprocess.run([sys.executable, str(SCRIPTS/'lab'), '--lab-home', str(SCRIPTS), 'status', 'x'], capture_output=True)
        self.assertNotEqual(p.returncode, 0)


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.split-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.wd = self.root/'work'
        self.exp = self.root/'lab/experiments/trial'
        self.pool = self.root/'pool.jsonl'
        self.run_lab('new', 'trial', '--workdir', str(self.wd), '--agent', 'command')
        self.write_pool(40)

    def run_lab(self, *args, success=True):
        p = subprocess.run([sys.executable, str(SCRIPTS/'lab'), '--lab-home',
                            str(self.root/'lab'), *args], capture_output=True, text=True)
        if success:
            self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
        else:
            self.assertNotEqual(p.returncode, 0, p.stdout+p.stderr)
        return p

    def write_pool(self, count):
        self.pool.write_text(''.join(json.dumps({'id': str(n), 'text': f'case {n}',
                                                'answer': 'café'})+'\n' for n in range(count)),
                             encoding='utf-8')

    def split(self, *args, success=True):
        return self.run_lab('split', 'trial', str(self.pool), *args, success=success)

    def manifest(self):
        return json.loads((self.exp/'split.json').read_text())

    def outputs(self):
        return [(self.wd/'development.jsonl').read_bytes(),
                (self.exp/'held-back.jsonl').read_bytes(), (self.exp/'split.json').read_bytes()]

    def no_outputs(self):
        for path in (self.wd/'development.jsonl', self.exp/'held-back.jsonl', self.exp/'split.json'):
            self.assertFalse(path.exists(), path)

    def baseline(self, success=True):
        cfg = json.loads((self.exp/'experiment.json').read_text())
        cfg.update(metric_cmd='echo 10', command='true', frozen=['development.jsonl'])
        (self.exp/'experiment.json').write_text(json.dumps(cfg))
        subprocess.run(['git', 'add', '-A'], cwd=self.wd, check=True, capture_output=True)
        subprocess.run(['git', '-c', 'user.name=lab', '-c', 'user.email=', 'commit',
                        '-qm', 'record cases'], cwd=self.wd, check=True, capture_output=True)
        return self.run_lab('baseline', 'trial', success=success)

    def test_default_split_counts_membership_and_hashes(self):
        result = self.split()
        record = self.manifest()
        self.assertEqual(record['seed'], 0)
        self.assertEqual(record['held_back_share'], 0.5)
        all_cases = []
        for key, path in [('development', self.wd/'development.jsonl'),
                          ('held_back', self.exp/'held-back.jsonl')]:
            cases = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(cases), 20)
            self.assertEqual(record[key]['count'], 20)
            self.assertEqual(record[key]['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(record[key]['path'], str(path))
            self.assertIn(str(path), result.stdout)
            all_cases.extend(cases)
        expected = [json.loads(line) for line in self.pool.read_text().splitlines()]
        self.assertEqual(sorted(all_cases, key=lambda x: x['id']), sorted(expected, key=lambda x: x['id']))
        self.assertEqual(record['source']['sha256'], hashlib.sha256(self.pool.read_bytes()).hexdigest())
        self.assertIn('split seed 0', result.stdout)
        self.assertEqual(record['source']['count'], 40)

    def test_reproducible_seed_and_explicit_replacement(self):
        self.split('--seed', '72')
        original = self.outputs()
        refused = self.split('--seed', '73', success=False)
        self.assertIn('--force', refused.stderr)
        self.assertEqual(self.outputs(), original)
        self.split('--seed', '72', '--force')
        self.assertEqual(self.outputs(), original)
        self.split('--seed', '73', '--force')
        self.assertNotEqual(self.outputs()[0], original[0])
        self.assertEqual(self.manifest()['seed'], 73)

    def test_share_and_odd_size(self):
        self.split('--held-back-share', '0.25')
        self.assertEqual(self.manifest()['development']['count'], 30)
        self.assertEqual(self.manifest()['held_back']['count'], 10)
        self.write_pool(100)
        self.split('--force', '--held-back-share', '0.29')
        self.assertEqual(self.manifest()['held_back']['count'], 29)
        self.write_pool(21)
        self.split('--force')
        self.assertEqual(self.manifest()['development']['count'], 11)
        self.assertEqual(self.manifest()['held_back']['count'], 10)

    def test_minimum_in_each_group(self):
        for count, share in [(0, '0.5'), (19, '0.5'), (40, '0.2'), (40, '0.8')]:
            with self.subTest(count=count, share=share):
                self.write_pool(count)
                p = self.split('--held-back-share', share, success=False)
                self.assertIn('each group needs at least 10 examples', p.stderr)
                self.no_outputs()
        self.write_pool(20)
        self.split()
        self.assertEqual(self.manifest()['development']['count'], 10)
        self.assertEqual(self.manifest()['held_back']['count'], 10)

    def test_invalid_shares(self):
        for share in ('0', '1', '-0.1', '1.1', 'nan', 'inf', 'not-a-number'):
            with self.subTest(share=share):
                self.split('--held-back-share', share, success=False)
                self.no_outputs()

    def test_invalid_json_and_ids(self):
        for line, message in [('{', 'valid JSON'), ('[]', 'JSON object'),
                              ('{"text":"missing"}', 'missing or invalid id'),
                              ('{"id":null}', 'missing or invalid id'),
                              ('{"id":" "}', 'missing or invalid id'),
                              ('{"id":true}', 'missing or invalid id'),
                              ('{"id":[]}', 'missing or invalid id'),
                              ('{"id":"extra","answer":NaN}', 'valid JSON'),
                              ('{"id":"0"}', 'duplicate id'),
                              ('{"id":0}', 'duplicate id')]:
            with self.subTest(line=line):
                self.write_pool(40)
                with self.pool.open('a') as source:
                    source.write(line+'\n')
                p = self.split(success=False)
                self.assertIn(message, p.stderr)
                self.no_outputs()

    def test_existing_destination_without_record(self):
        for path in (self.wd/'development.jsonl', self.exp/'held-back.jsonl', self.exp/'split.json'):
            with self.subTest(path=path):
                path.write_text('preserve me')
                self.split(success=False)
                self.assertEqual(path.read_text(), 'preserve me')
                path.unlink()
                self.no_outputs()

    def test_invalid_replacement_preserves_existing_split(self):
        self.split()
        original = self.outputs()
        self.write_pool(19)
        self.split('--force', success=False)
        self.assertEqual(self.outputs(), original)

    def test_destination_symlinks_and_directories_are_refused(self):
        held = self.exp/'held-back.jsonl'
        held.symlink_to(self.pool)
        original = self.pool.read_bytes()
        p = self.split('--force', success=False)
        self.assertIn('must not be a symlink', p.stderr)
        self.assertEqual(self.pool.read_bytes(), original)
        held.unlink()
        held.mkdir()
        p = self.split('--force', success=False)
        self.assertIn('must be a file', p.stderr)
        self.assertFalse((self.wd/'development.jsonl').exists())

    def test_held_back_destinations_inside_work_or_skill_are_refused(self):
        for target, message in [(self.wd/'leak.jsonl', 'outside the working copy'),
                                (SCRIPTS.parent/'leak.jsonl', 'outside the skill folder')]:
            with self.subTest(target=target):
                held = self.exp/'held-back.jsonl'
                held.symlink_to(target)
                p = self.split('--force', success=False)
                self.assertIn(message, p.stderr)
                self.assertFalse(target.exists())
                held.unlink()
                self.no_outputs()

    def test_records_inside_working_copy_are_refused(self):
        cfg = json.loads((self.exp/'experiment.json').read_text())
        cfg['workdir'] = str(self.root)
        (self.exp/'experiment.json').write_text(json.dumps(cfg))
        p = self.split(success=False)
        self.assertIn('outside the working copy', p.stderr)
        self.no_outputs()

    def test_parent_symlink_into_working_copy_is_refused(self):
        target = self.wd/'records'
        self.exp.rename(target)
        self.exp.symlink_to(target, target_is_directory=True)
        p = self.split('--force', success=False)
        self.assertIn('outside the working copy', p.stderr)
        self.no_outputs()

    def test_source_pool_must_stay_outside_working_copy(self):
        self.pool.rename(self.wd/'pool.jsonl')
        self.pool = self.wd/'pool.jsonl'
        p = self.split(success=False)
        self.assertIn('full pool of cases outside', p.stderr)
        self.no_outputs()

    def test_baseline_records_split_and_freezes_it(self):
        self.split('--seed', '91')
        record = self.manifest()
        result = self.baseline()
        self.assertIn('split seed 91: 20 development, 20 held-back', result.stdout)
        self.assertEqual(json.loads((self.exp/'baseline-split.json').read_text()), record)
        baseline = (self.exp/'attempts/000-baseline.md').read_text()
        self.assertIn(record['held_back']['sha256'], baseline)
        original = self.outputs()
        p = self.split('--force', success=False)
        self.assertIn('baseline already exists', p.stderr)
        self.assertEqual(self.outputs(), original)
        self.run_lab('run', 'trial', '--tries', '1')
        (self.exp/'split.json').unlink()
        p = self.run_lab('run', 'trial', '--tries', '1', success=False)
        self.assertIn('differs from baseline', p.stderr)

    def test_changed_cases_rejected_before_baseline(self):
        self.split()
        original = self.outputs()
        for path in (self.wd/'development.jsonl', self.exp/'held-back.jsonl'):
            with self.subTest(path=path):
                path.write_text('changed')
                cfg = json.loads((self.exp/'experiment.json').read_text())
                with self.assertRaisesRegex(ValueError, 'differ from split.json'):
                    lab.checked_split(self.exp, cfg)
                (self.wd/'development.jsonl').write_bytes(original[0])
                (self.exp/'held-back.jsonl').write_bytes(original[1])
        self.baseline()
        (self.exp/'held-back.jsonl').write_text('changed')
        p = self.run_lab('run', 'trial', '--tries', '1', success=False)
        self.assertIn('differ from split.json', p.stderr)

    def test_baseline_refuses_changed_split_files(self):
        self.split()
        (self.exp/'held-back.jsonl').write_text('changed')
        p = self.baseline(success=False)
        self.assertIn('differ from split.json', p.stderr)
        self.assertFalse((self.exp/'results.tsv').exists())


class AgentTests(unittest.TestCase):
    def test_codex_model_selection(self):
        with mock.patch.object(agents, 'execute', return_value=(0, '', '')) as execute:
            for model in (None, '', 'chosen-model'):
                with self.subTest(model=model):
                    agents.ask('prompt', agent='codex', model=model)
                    args = execute.call_args.args[0]
                    if model:
                        self.assertEqual(args[args.index('--model')+1], model)
                    else:
                        self.assertNotIn('--model', args)
                    self.assertEqual(args[-1], '-')


class ToyRunnerTests(unittest.TestCase):
    def run_toy(self, agent, fail_setup=False, fail_agent=False):
        with tempfile.TemporaryDirectory(prefix='.toy-test-') as tmp:
            root = Path(tmp)
            env = dict(os.environ, TRIES='1', FAIL_SETUP=str(int(fail_setup)),
                       FAIL_AGENT=str(int(fail_agent)))
            # Check inherited configuration locations without accessing their files.
            locations = {key: value for key, value in env.items()
                         if key == 'HOME' or key.endswith(('_HOME', '_CONFIG_DIR'))}
            env['TOY_EXPECTED_LOCATIONS'] = json.dumps(locations)
            fakebin = root/'bin'
            fakebin.mkdir()
            fake = f'''#!{sys.executable}
import json
import os
from pathlib import Path
import sys
if Path(sys.argv[0]).name == 'python3':
    if (os.environ['FAIL_SETUP'] == '1' and len(sys.argv) > 2
            and Path(sys.argv[1]).name == 'lab' and 'new' in sys.argv[2:]):
        sys.exit(23)
    os.execv({sys.executable!r}, [{sys.executable!r}, *sys.argv[1:]])
locations = {{key: value for key, value in os.environ.items()
              if key == 'HOME' or key.endswith(('_HOME', '_CONFIG_DIR'))}}
if locations != json.loads(os.environ['TOY_EXPECTED_LOCATIONS']):
    sys.exit('inherited configuration location changed')
Path('ATTEMPT.md').write_text(Path(sys.argv[0]).name + ': inherited configuration retained')
sys.exit(23 if os.environ['FAIL_AGENT'] == '1' else 0)
'''
            for name in ('python3', 'claude', 'codex'):
                (fakebin/name).write_text(fake)
                (fakebin/name).chmod(0o755)
            env['PATH'] = str(fakebin)+os.pathsep+env['PATH']
            dest = root/'toy output'
            p = subprocess.run(['bash', str(SCRIPTS.parent/'examples/toy/run.sh'), agent, str(dest)],
                               env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(p.returncode, 23 if fail_setup else 0, p.stdout+p.stderr)
            if not fail_setup:
                split = json.loads((dest/'lab/experiments/toy/split.json').read_text())
                self.assertEqual(split['development']['count'], 12)
                self.assertEqual(split['held_back']['count'], 12)
                self.assertEqual(split['seed'], 0)
                self.assertEqual(json.loads((dest/'lab/experiments/toy/baseline-split.json').read_text()), split)
                rows = list(csv.DictReader(
                    (dest/'lab/experiments/toy/results.tsv').read_text().splitlines(),
                    delimiter='\t'))
                self.assertEqual(len(rows), 2)
                self.assertEqual(rows[0]['verdict'], 'baseline')
                expected = 'bin: agent failed (23)' if fail_agent else 'bin: no change'
                self.assertEqual(rows[1]['verdict'], expected)
                self.assertIn('baseline', p.stdout)
                self.assertIn(expected, p.stdout)
                record = (dest/'lab/experiments/toy/attempts/001.md').read_text()
                self.assertIn(agent + ': inherited configuration retained', record)
            self.assertEqual({p.name for p in (dest/'runtime').iterdir()}, {'tmp'})

    def test_inherited_configuration(self):
        for agent in ('codex', 'claude'):
            with self.subTest(agent=agent):
                self.run_toy(agent)

    def test_agent_failure_is_recorded(self):
        for agent in ('codex', 'claude'):
            with self.subTest(agent=agent):
                self.run_toy(agent, fail_agent=True)

    def test_setup_failure_preserves_exit_status(self):
        for agent in ('codex', 'claude'):
            with self.subTest(agent=agent):
                self.run_toy(agent, fail_setup=True)


class JudgeTests(unittest.TestCase):
    def test_finite_numbers(self):
        for text, want in [('1e-3', .001), ('notes\n-2.5', -2.5), ('nan', None), ('inf', None), ('', None), ('3 items', None)]:
            self.assertEqual(lab.last_number(text), want)

    def test_command_judges(self):
        with tempfile.TemporaryDirectory(prefix='.judge-test-') as tmp:
            root = Path(tmp)
            for name in ('source', 'a', 'b'):
                (root/name).write_text('{"id":"one","text":"hello"}\n')
            (root/'rubric').write_text('Preserve meaning.')
            def run(script, args, command):
                return subprocess.run([sys.executable, str(SCRIPTS/script), *args,
                    '--rubric', str(root/'rubric'), '--agent', 'command', '--command', command],
                    cwd=root, capture_output=True, text=True)
            teacher = run('teacher.py', ['source', 'gold'], '''printf '%s\n' '{"id":"one","text":"hello"}' ''')
            self.assertEqual(teacher.returncode, 0, teacher.stderr)
            self.assertEqual(json.loads((root/'gold').read_text())['text'], 'hello')
            pair = run('pairwise.py', ['source', 'a', 'b'], '''printf '%s\n' '{"id":"one","pick":"X"}' ''')
            self.assertEqual(pair.returncode, 0, pair.stderr)
            self.assertEqual(pair.stdout.splitlines()[-1], '50.0')  # positional bias becomes tie
            broken = run('pairwise.py', ['source', 'a', 'b'], 'echo malformed')
            self.assertNotEqual(broken.returncode, 0)
            distance = subprocess.run([sys.executable, str(SCRIPTS/'text_distance.py'), 'a', 'gold'], cwd=root, capture_output=True, text=True)
            self.assertEqual(distance.returncode, 0, distance.stderr)
            self.assertEqual(distance.stdout.splitlines()[-1], '0.000')


if __name__ == '__main__':
    unittest.main()
