"""Offline, clean-venv rehearsal of the fixed source-bound validation contract."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from check_results import verify

REMOTE_CANDIDATE = '014784d0ae33d91375098e91d16c42077d8895ff'
BASE = '31a4d36d123688581a9e9744427272b33ce940e0'
TREE = '1b98155da4d11a037421d190aa612504414505ab'
CANDIDATE_HASHES = {
    'qwen_agent/llm/base.py': '8ab24fad5d8002ed7c73b27ba55bf8c6403519fd09d852c48b4bb56aab54c8c7',
    'tests/llm/test_context_truncation.py': '286242e7195129d3af90b363c15daa6f5489d6b697d67737703b1468a80b351b',
}
parser = argparse.ArgumentParser()
parser.add_argument('--python', type=Path, required=True)
parser.add_argument('--candidate', type=Path, required=True)
parser.add_argument('--baseline', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--profile', choices=['current', 'gui', 'minimum'], required=True)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--candidate-sha')
group.add_argument('--local-tree-only', action='store_true')
args = parser.parse_args()
python = args.python.absolute()
candidate = args.candidate.resolve()
baseline = args.baseline.resolve()
out = args.out.resolve()
out.mkdir(parents=True, exist_ok=False)
harness = Path(__file__).resolve().parent
if args.candidate_sha:
    assert re.fullmatch(r'[0-9a-f]{40}', args.candidate_sha)
    assert args.candidate_sha == REMOTE_CANDIDATE
for path, expected in CANDIDATE_HASHES.items():
    assert hashlib.sha256((candidate / path).read_bytes()).hexdigest() == expected, path
assert hashlib.sha256((baseline / 'qwen_agent/llm/base.py').read_bytes()).hexdigest() == '2cbf81cf2f9035c2d6013f11f7ceff8dc141eb9329fcd8ba1617eeb59cd6d7ae'
expected_versions = {
    'current': ('2.13.4', '2.46.4', '3.24.0'),
    'gui': ('2.9.2', '2.23.4', '3.24.0'),
    'minimum': ('2.3.0', '2.6.3', '1.30.5'),
}[args.profile]
records = []


def run(name, command, source=candidate):
    state = out / name
    state.mkdir()
    for folder in ('home', 'tmp', 'workspace', 'tokenizer-cache', 'pycache'):
        (state / folder).mkdir()
    env = {
        'HOME': str(state / 'home'),
        'PATH': str(python.parent) + ':/usr/bin:/bin',
        'TMPDIR': str(state / 'tmp'),
        'PYTHONPATH': str(source),
        'PYTHONNOUSERSITE': '1',
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONPYCACHEPREFIX': str(state / 'pycache'),
        'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
        'TIKTOKEN_CACHE_DIR': str(state / 'tokenizer-cache'),
        'QWEN_AGENT_DEFAULT_WORKSPACE': str(state / 'workspace'),
        'QWEN_AGENT_DEFAULT_RAG_SEARCHERS': "['keyword_search', 'front_page_search']",
    }
    (state / 'command.json').write_text(json.dumps({'command': command, 'cwd': str(candidate), 'environment': env}, indent=2) + '\n')
    result = subprocess.run(command, cwd=candidate, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (state / 'output.log').write_text(result.stdout)
    (state / 'exit.txt').write_text(str(result.returncode) + '\n')
    records.append({'name': name, 'exit': result.returncode})
    print(name, 'exit', result.returncode, flush=True)
    print(result.stdout, flush=True)
    return result.returncode


for phase in ('cold', 'baseline', 'candidate'):
    source = baseline if phase == 'baseline' else candidate
    guard_path = out / (phase + '.guard.json')
    junit = out / (phase + '.xml')
    code = run(phase, [str(python), str(harness / 'guarded_pytest.py'), '--source', str(source), '--tests', str(candidate), '--phase', phase, '--junit', str(junit), '--result', str(guard_path)], source)
    guard = json.loads(guard_path.read_text())
    assert tuple(guard['versions'][name] for name in ('pydantic', 'pydantic-core', 'openai')) == expected_versions
    assert guard['guard_ok'] and guard['tokenizer_cache_empty']
    if phase == 'cold':
        assert code == 0
    else:
        summary = verify(junit.read_text(), phase, code, guard)
        (out / (phase + '.verified.json')).write_text(json.dumps(summary, indent=2) + '\n')
        print('STRICT_RESULT:', json.dumps(summary), flush=True)

changed = ['qwen_agent/llm/base.py', 'tests/llm/test_context_truncation.py']
checks = [
    ('flake8', ['-m', 'flake8', '--max-line-length=300', '--extend-ignore=E231,E702,E251,W604'] + changed),
    ('isort', ['-m', 'isort', '--check-only', '--diff', '--line-length', '120'] + changed),
    ('yapf', ['-m', 'yapf', '--diff', '--style', '{based_on_style: google, column_limit: 120}'] + changed),
    ('compileall', ['-m', 'compileall', '-q', 'qwen_agent', 'tests']),
    ('pip-check', ['-m', 'pip', 'check']),
    ('pip-freeze', ['-m', 'pip', 'freeze', '--all']),
]
for name, command in checks:
    assert run(name, [str(python)] + command) == 0, name
for path, expected in CANDIDATE_HASHES.items():
    assert hashlib.sha256((candidate / path).read_bytes()).hexdigest() == expected, 'Source changed during validation: ' + path
report = {
    'base': BASE, 'candidate_commit': args.candidate_sha, 'candidate_tree': TREE,
    'local_tree_rehearsal': args.local_tree_only,
    'profile': args.profile, 'checks': records,
    'baseline_expected': {'failed': 7, 'passed': 9}, 'candidate_expected': {'failed': 0, 'passed': 22},
    'boundary': 'Reviewed Python paths with fake provider transport and Python audit guards; not OS isolation.',
}
(out / 'SUMMARY.json').write_text(json.dumps(report, indent=2) + '\n')
print('VALIDATION_COMPLETE:', json.dumps(report), flush=True)
