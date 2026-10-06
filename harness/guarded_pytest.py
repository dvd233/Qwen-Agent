"""Run reviewed local tests with Python-level network/process guards, not OS isolation."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import socket
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--tests', type=Path, required=True)
parser.add_argument('--phase', choices=['cold', 'baseline', 'candidate'], required=True)
parser.add_argument('--junit', type=Path)
parser.add_argument('--result', type=Path, required=True)
args = parser.parse_args()
source = args.source.resolve()
tests = args.tests.resolve()
assert sys.prefix != sys.base_prefix, 'Use the dedicated clean venv.'
assert 'include-system-site-packages = false' in (Path(sys.prefix) / 'pyvenv.cfg').read_text()
assert os.environ.get('PYTEST_DISABLE_PLUGIN_AUTOLOAD') == '1'
assert os.environ.get('PYTHONPATH') == str(source)
assert not list(Path(os.environ['TIKTOKEN_CACHE_DIR']).iterdir()), 'Each phase starts with an empty tokenizer cache.'

vocab = source / 'qwen_agent/utils/qwen.tiktoken'
assert hashlib.sha256(vocab.read_bytes()).hexdigest() == 'b2b1b8dfb5cc5f024bafc373121c6aba3f66f9a5a0269e243470a1de16a33186'
blocked = []
vocab_reads = []
self_testing = True


def audit(event, audit_args):
    if event == 'open' and isinstance(audit_args[0], str) and audit_args[0].endswith('qwen.tiktoken'):
        vocab_reads.append(str(Path(audit_args[0]).resolve()))
    if (event.startswith('socket.') and event != 'socket.__new__') or event.startswith('subprocess.') or event in (
            'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.fork'):
        ipv6_probe = event == 'socket.bind' and len(audit_args) > 1 and audit_args[1] == ('::1', 0)
        blocked.append({'event': event, 'allowed_import_probe': ipv6_probe, 'guard_self_test': self_testing})
        raise AssertionError('Offline Python guard blocked ' + event)


sys.addaudithook(audit)
# These calls must fail before any connection, resolver call or subprocess occurs.
with socket.socket() as sock:
    try:
        sock.connect(('127.0.0.1', 9))
    except AssertionError:
        pass
    else:
        raise AssertionError('Socket guard is ineffective.')
try:
    socket.getaddrinfo('example.invalid', 443)
except AssertionError:
    pass
else:
    raise AssertionError('DNS guard is ineffective.')
import subprocess
try:
    subprocess.run([sys.executable, '-c', 'raise SystemExit(99)'], check=False)
except AssertionError:
    pass
else:
    raise AssertionError('Process guard is ineffective.')
self_testing = False

from qwen_agent.llm import base
from qwen_agent.utils.tokenization_qwen import tokenizer

assert Path(base.__file__).resolve() == source / 'qwen_agent/llm/base.py'
assert vocab_reads == [str(vocab)], f'Unexpected vocabulary reads: {vocab_reads}'
assert tokenizer.count_tokens('offline tokenizer probe') > 0
assert not list(Path(os.environ['TIKTOKEN_CACHE_DIR']).iterdir())

status = 0
if args.phase != 'cold':
    import pytest
    nodes = [str(tests / 'tests/llm/test_context_truncation.py')]
    if args.phase == 'candidate':
        nodes += [
            str(tests / 'tests/tools/test_keyword_search.py') + '::test_keyword_search',
            str(tests / 'tests/tools/test_hybrid_search.py') + '::test_hybrid_search',
            str(tests / 'tests/tools/test_tools.py') + '::test_storage_put[put]',
            str(tests / 'tests/tools/test_tools.py') + '::test_storage_scan[scan]',
            str(tests / 'tests/tools/test_tools.py') + '::test_storage_get_delete[get]',
            str(tests / 'tests/tools/test_tools.py') + '::test_storage_get_delete[delete]',
        ]
    status = pytest.main(['-q', '--rootdir=' + str(tests), '--junitxml=' + str(args.junit)] + nodes)

unexpected = [item for item in blocked if not item['guard_self_test'] and not item['allowed_import_probe']]
result = {
    'phase': args.phase,
    'source_module': str(Path(base.__file__).resolve()),
    'python': sys.version,
    'venv': sys.prefix,
    'system_site_packages': False,
    'versions': {name: importlib.metadata.version(name) for name in ('pydantic', 'pydantic-core', 'openai', 'dashscope', 'tiktoken', 'pytest')},
    'vocabulary_reads': vocab_reads,
    'tokenizer_cache_empty': not list(Path(os.environ['TIKTOKEN_CACHE_DIR']).iterdir()),
    'blocked_events': blocked,
    'unexpected_guard_events': unexpected,
    'pytest_exit': int(status),
    'guard_ok': not unexpected,
}
args.result.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
if unexpected:
    raise SystemExit(2)
raise SystemExit(status)
