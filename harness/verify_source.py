"""Verify the dispatched feature commit before running its source-bound validation."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

CANDIDATE = '014784d0ae33d91375098e91d16c42077d8895ff'
BASE = '31a4d36d123688581a9e9744427272b33ce940e0'
TREE = '1b98155da4d11a037421d190aa612504414505ab'
FILES = {
    'qwen_agent/llm/base.py': '8ab24fad5d8002ed7c73b27ba55bf8c6403519fd09d852c48b4bb56aab54c8c7',
    'tests/llm/test_context_truncation.py': '286242e7195129d3af90b363c15daa6f5489d6b697d67737703b1468a80b351b',
}
parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--candidate-sha', required=True)
args = parser.parse_args()
assert re.fullmatch(r'[0-9a-f]{40}', args.candidate_sha), 'Pass the exact final feature SHA.'
assert args.candidate_sha == CANDIDATE, 'This validation snapshot is bound to the reviewed published commit.'


def git(*items):
    return subprocess.check_output(['git', '-C', str(args.repo), *items], text=True).strip()


assert git('rev-parse', 'HEAD') == args.candidate_sha
assert git('rev-parse', 'HEAD^{tree}') == TREE
assert git('show', '-s', '--format=%P', 'HEAD') == BASE, 'Expected one feature commit directly on the fixed base.'
assert git('diff', '--name-status', BASE, 'HEAD').splitlines() == [
    'M\tqwen_agent/llm/base.py', 'A\ttests/llm/test_context_truncation.py'
]
assert git('status', '--porcelain') == '', 'Candidate checkout must be pristine.'
assert git('ls-tree', 'HEAD', '--', *FILES).splitlines() == [
    '100755 blob 1c8dff867e0cfc230ab5e122cd00cf10c2d16a97\tqwen_agent/llm/base.py',
    '100644 blob a2c8db3f9319f8887c05230872814c305eefe766\ttests/llm/test_context_truncation.py',
], 'File modes or blobs differ from the reviewed tree.'
for path, expected in FILES.items():
    assert hashlib.sha256((args.repo / path).read_bytes()).hexdigest() == expected, path
print(json.dumps({'candidate_commit': args.candidate_sha, 'candidate_tree': TREE, 'base': BASE, 'changed_files': FILES}, indent=2))
