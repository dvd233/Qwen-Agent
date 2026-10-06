"""Strict source-bound baseline/candidate JUnit outcome assertions."""
import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

MODULE = 'tests.llm.test_context_truncation'
NAMES = set()
for stem in ('test_truncated_tool_result_preserves_metadata', 'test_large_budget_leaves_tool_messages_unchanged'):
    for representation in ('string', 'text_items'):
        for location in ('latest', 'earlier'):
            NAMES.add(f'{stem}[{representation}-{location}]')
for representation in ('string', 'text_items'):
    for budget in ('truncated', 'untruncated'):
        NAMES.add(f'test_chat_preserves_tool_result_id_with_fake_transport[{representation}-{budget}]')
NAMES |= {
    'test_non_tool_truncation_keeps_existing_behavior[user]',
    'test_non_tool_truncation_keeps_existing_behavior[assistant]',
    'test_oversized_assistant_call_keeps_existing_budget_behavior',
    'test_truncated_tool_result_only_adds_routing_metadata',
}
BASELINE = {(MODULE, name) for name in NAMES}
CANDIDATE = BASELINE | {
    ('tests.tools.test_keyword_search', 'test_keyword_search'),
    ('tests.tools.test_hybrid_search', 'test_hybrid_search'),
    ('tests.tools.test_tools', 'test_storage_put[put]'),
    ('tests.tools.test_tools', 'test_storage_scan[scan]'),
    ('tests.tools.test_tools', 'test_storage_get_delete[get]'),
    ('tests.tools.test_tools', 'test_storage_get_delete[delete]'),
}
FAILURES = {}
for name in NAMES:
    if name.startswith('test_truncated_tool_result_preserves_metadata[') or name == 'test_truncated_tool_result_only_adds_routing_metadata':
        FAILURES[(MODULE, name)] = "AssertionError: assert None == 'read_report'"
    if name.startswith('test_chat_preserves_tool_result_id_with_fake_transport[') and name.endswith('-truncated]'):
        FAILURES[(MODULE, name)] = "AssertionError: assert 'call_report' == '1'"
assert len(BASELINE) == 16 and len(FAILURES) == 7 and len(CANDIDATE) == 22

# Complete diagnostics from the public synthetic fixtures. All three pinned
# dependency profiles produce identical diagnostics after normalizing only the
# address on the exact pytest MonkeyPatch fixture-repr line. No paths, arbitrary
# hexadecimal values, whitespace or exception text are removed.
EXPECTED_FAILURES = json.loads(r'''
{
  "test_truncated_tool_result_preserves_metadata[string-latest]": {
    "message": "AssertionError: assert None == 'read_report'\n +  where None = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...rt data report data report data report data report data report data report data report data report data report data '}).name\n +  and   'read_report' = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...eport data report data ', 'name': 'read_report', 'extra': {'function_id': 'call_report', 'source': {'pages': [1, 2]}}}).name",
    "text": "earlier_result = False, content_items = False\n\n    @pytest.mark.parametrize('earlier_result', [False, True], ids=['latest', 'earlier'])\n    @pytest.mark.parametrize('content_items', [False, True], ids=['string', 'text_items'])\n    def test_truncated_tool_result_preserves_metadata(earlier_result, content_items):\n        messages = tool_messages(earlier_result, content_items)\n        before = copy.deepcopy(messages)\n    \n        result = _truncate_input_messages_roughly(messages, max_tokens=100)\n        tool_result = next(msg for msg in result if msg.role == 'function')\n    \n        assert messages == before\n        assert isinstance(tool_result.content, str)\n        assert tokenizer.count_tokens(tool_result.content) < tokenizer.count_tokens('report data ' * 100)\n>       assert tool_result.name == before[2].name\nE       AssertionError: assert None == 'read_report'\nE        +  where None = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...rt data report data report data report data report data report data report data report data report data report data '}).name\nE        +  and   'read_report' = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...eport data report data ', 'name': 'read_report', 'extra': {'function_id': 'call_report', 'source': {'pages': [1, 2]}}}).name\n\ntests/llm/test_context_truncation.py:78: AssertionError"
  },
  "test_truncated_tool_result_preserves_metadata[string-earlier]": {
    "message": "AssertionError: assert None == 'read_report'\n +  where None = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...rt data report data report data report data report data report data report data report data report data report data '}).name\n +  and   'read_report' = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...eport data report data ', 'name': 'read_report', 'extra': {'function_id': 'call_report', 'source': {'pages': [1, 2]}}}).name",
    "text": "earlier_result = True, content_items = False\n\n    @pytest.mark.parametrize('earlier_result', [False, True], ids=['latest', 'earlier'])\n    @pytest.mark.parametrize('content_items', [False, True], ids=['string', 'text_items'])\n    def test_truncated_tool_result_preserves_metadata(earlier_result, content_items):\n        messages = tool_messages(earlier_result, content_items)\n        before = copy.deepcopy(messages)\n    \n        result = _truncate_input_messages_roughly(messages, max_tokens=100)\n        tool_result = next(msg for msg in result if msg.role == 'function')\n    \n        assert messages == before\n        assert isinstance(tool_result.content, str)\n        assert tokenizer.count_tokens(tool_result.content) < tokenizer.count_tokens('report data ' * 100)\n>       assert tool_result.name == before[2].name\nE       AssertionError: assert None == 'read_report'\nE        +  where None = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...rt data report data report data report data report data report data report data report data report data report data '}).name\nE        +  and   'read_report' = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...eport data report data ', 'name': 'read_report', 'extra': {'function_id': 'call_report', 'source': {'pages': [1, 2]}}}).name\n\ntests/llm/test_context_truncation.py:78: AssertionError"
  },
  "test_truncated_tool_result_preserves_metadata[text_items-latest]": {
    "message": "AssertionError: assert None == 'read_report'\n +  where None = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...rt data report data report data report data report data report data report data report data report data report data '}).name\n +  and   'read_report' = Message({'role': 'function', 'content': [{'text': 'report data report data report data report data report data report ...ort data report data '}], 'name': 'read_report', 'extra': {'function_id': 'call_report', 'source': {'pages': [1, 2]}}}).name",
    "text": "earlier_result = False, content_items = True\n\n    @pytest.mark.parametrize('earlier_result', [False, True], ids=['latest', 'earlier'])\n    @pytest.mark.parametrize('content_items', [False, True], ids=['string', 'text_items'])\n    def test_truncated_tool_result_preserves_metadata(earlier_result, content_items):\n        messages = tool_messages(earlier_result, content_items)\n        before = copy.deepcopy(messages)\n    \n        result = _truncate_input_messages_roughly(messages, max_tokens=100)\n        tool_result = next(msg for msg in result if msg.role == 'function')\n    \n        assert messages == before\n        assert isinstance(tool_result.content, str)\n        assert tokenizer.count_tokens(tool_result.content) < tokenizer.count_tokens('report data ' * 100)\n>       assert tool_result.name == before[2].name\nE       AssertionError: assert None == 'read_report'\nE        +  where None = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...rt data report data report data report data report data report data report data report data report data report data '}).name\nE        +  and   'read_report' = Message({'role': 'function', 'content': [{'text': 'report data report data report data report data report data report ...ort data report data '}], 'name': 'read_report', 'extra': {'function_id': 'call_report', 'source': {'pages': [1, 2]}}}).name\n\ntests/llm/test_context_truncation.py:78: AssertionError"
  },
  "test_truncated_tool_result_preserves_metadata[text_items-earlier]": {
    "message": "AssertionError: assert None == 'read_report'\n +  where None = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...rt data report data report data report data report data report data report data report data report data report data '}).name\n +  and   'read_report' = Message({'role': 'function', 'content': [{'text': 'report data report data report data report data report data report ...ort data report data '}], 'name': 'read_report', 'extra': {'function_id': 'call_report', 'source': {'pages': [1, 2]}}}).name",
    "text": "earlier_result = True, content_items = True\n\n    @pytest.mark.parametrize('earlier_result', [False, True], ids=['latest', 'earlier'])\n    @pytest.mark.parametrize('content_items', [False, True], ids=['string', 'text_items'])\n    def test_truncated_tool_result_preserves_metadata(earlier_result, content_items):\n        messages = tool_messages(earlier_result, content_items)\n        before = copy.deepcopy(messages)\n    \n        result = _truncate_input_messages_roughly(messages, max_tokens=100)\n        tool_result = next(msg for msg in result if msg.role == 'function')\n    \n        assert messages == before\n        assert isinstance(tool_result.content, str)\n        assert tokenizer.count_tokens(tool_result.content) < tokenizer.count_tokens('report data ' * 100)\n>       assert tool_result.name == before[2].name\nE       AssertionError: assert None == 'read_report'\nE        +  where None = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...rt data report data report data report data report data report data report data report data report data report data '}).name\nE        +  and   'read_report' = Message({'role': 'function', 'content': [{'text': 'report data report data report data report data report data report ...ort data report data '}], 'name': 'read_report', 'extra': {'function_id': 'call_report', 'source': {'pages': [1, 2]}}}).name\n\ntests/llm/test_context_truncation.py:78: AssertionError"
  },
  "test_chat_preserves_tool_result_id_with_fake_transport[string-truncated]": {
    "message": "AssertionError: assert 'call_report' == '1'\n  \n  - 1\n  + call_report",
    "text": "monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at ADDRESS>\nmax_tokens = 100, content_items = False\n\n    @pytest.mark.parametrize('max_tokens', [100, 10000], ids=['truncated', 'untruncated'])\n    @pytest.mark.parametrize('content_items', [False, True], ids=['string', 'text_items'])\n    def test_chat_preserves_tool_result_id_with_fake_transport(monkeypatch, max_tokens, content_items):\n        model = TextChatAtOAI({\n            'model': 'offline-test',\n            'model_type': 'oai',\n            'api_key': 'EMPTY',\n            'generate_cfg': {\n                'use_raw_api': True,\n                'max_input_tokens': max_tokens\n            },\n        })\n        captured = []\n    \n        def fake_create(**kwargs):\n            captured.append(kwargs['messages'])\n            delta = SimpleNamespace(content='done', reasoning_content=None, tool_calls=None)\n            return iter([SimpleNamespace(choices=[SimpleNamespace(delta=delta)])])\n    \n        monkeypatch.setattr(model, '_chat_complete_create', fake_create)\n        messages = tool_messages(content_items=content_items)\n        before = copy.deepcopy(messages)\n    \n        response = list(model.chat(messages=messages, stream=True))\n    \n        assert response[-1][-1].content == 'done'\n        assert messages == before\n        assert len(captured) == 1\n        request = captured[0]\n        assistant_call = next(msg for msg in request if msg['role'] == 'assistant')\n        tool_result = next(msg for msg in request if msg['role'] == 'tool')\n        # Accept either wire-field spelling; this test concerns preservation of the identifier value.\n        result_id = tool_result.get('tool_call_id', tool_result.get('id'))\n>       assert assistant_call['tool_calls'][0]['id'] == result_id == 'call_report'\nE       AssertionError: assert 'call_report' == '1'\nE         \nE         - 1\nE         + call_report\n\ntests/llm/test_context_truncation.py:136: AssertionError"
  },
  "test_chat_preserves_tool_result_id_with_fake_transport[text_items-truncated]": {
    "message": "AssertionError: assert 'call_report' == '1'\n  \n  - 1\n  + call_report",
    "text": "monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at ADDRESS>\nmax_tokens = 100, content_items = True\n\n    @pytest.mark.parametrize('max_tokens', [100, 10000], ids=['truncated', 'untruncated'])\n    @pytest.mark.parametrize('content_items', [False, True], ids=['string', 'text_items'])\n    def test_chat_preserves_tool_result_id_with_fake_transport(monkeypatch, max_tokens, content_items):\n        model = TextChatAtOAI({\n            'model': 'offline-test',\n            'model_type': 'oai',\n            'api_key': 'EMPTY',\n            'generate_cfg': {\n                'use_raw_api': True,\n                'max_input_tokens': max_tokens\n            },\n        })\n        captured = []\n    \n        def fake_create(**kwargs):\n            captured.append(kwargs['messages'])\n            delta = SimpleNamespace(content='done', reasoning_content=None, tool_calls=None)\n            return iter([SimpleNamespace(choices=[SimpleNamespace(delta=delta)])])\n    \n        monkeypatch.setattr(model, '_chat_complete_create', fake_create)\n        messages = tool_messages(content_items=content_items)\n        before = copy.deepcopy(messages)\n    \n        response = list(model.chat(messages=messages, stream=True))\n    \n        assert response[-1][-1].content == 'done'\n        assert messages == before\n        assert len(captured) == 1\n        request = captured[0]\n        assistant_call = next(msg for msg in request if msg['role'] == 'assistant')\n        tool_result = next(msg for msg in request if msg['role'] == 'tool')\n        # Accept either wire-field spelling; this test concerns preservation of the identifier value.\n        result_id = tool_result.get('tool_call_id', tool_result.get('id'))\n>       assert assistant_call['tool_calls'][0]['id'] == result_id == 'call_report'\nE       AssertionError: assert 'call_report' == '1'\nE         \nE         - 1\nE         + call_report\n\ntests/llm/test_context_truncation.py:136: AssertionError"
  },
  "test_truncated_tool_result_only_adds_routing_metadata": {
    "message": "AssertionError: assert None == 'read_report'\n +  where None = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...rt data report data report data report data report data report data report data report data report data report data '}).name",
    "text": "def test_truncated_tool_result_only_adds_routing_metadata():\n        messages = tool_messages()\n        messages[2].reasoning_content = 'not a tool result field'\n        messages[2].function_call = FunctionCall(name='not_a_tool_result', arguments='{}')\n        before = copy.deepcopy(messages)\n    \n        result = _truncate_input_messages_roughly(messages, max_tokens=100)\n        tool_result = next(msg for msg in result if msg.role == 'function')\n    \n        assert messages == before\n>       assert tool_result.name == 'read_report'\nE       AssertionError: assert None == 'read_report'\nE        +  where None = Message({'role': 'function', 'content': 'report data report data report data report data report data report data repor...rt data report data report data report data report data report data report data report data report data report data '}).name\n\ntests/llm/test_context_truncation.py:206: AssertionError"
  }
}
''')
assert set(EXPECTED_FAILURES) == {name for _, name in FAILURES}


def normalize_diagnostic(text):
    assert isinstance(text, str), 'Missing failure diagnostic.'
    return re.sub(r'(?m)^monkeypatch = <_pytest\.monkeypatch\.MonkeyPatch object at 0x[0-9a-f]+>$',
                  'monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at ADDRESS>', text)


def verify(junit, phase, process_exit, guard):
    expected = BASELINE if phase == 'baseline' else CANDIDATE
    expected_failures = FAILURES if phase == 'baseline' else {}
    assert process_exit == (1 if phase == 'baseline' else 0), f'Unexpected process exit: {process_exit}'
    assert guard['phase'] == phase and guard['guard_ok'] and not guard['unexpected_guard_events']
    assert guard['pytest_exit'] == process_exit
    root = ET.fromstring(junit)
    assert root.tag in ('testsuite', 'testsuites'), 'Unexpected JUnit root.'
    assert not list(root.iter('error')), 'Unexpected error outside or inside a testcase.'
    assert not list(root.iter('skipped')), 'Unexpected skipped test.'
    assert len(list(root.iter('failure'))) == len(expected_failures), 'Wrong total failure-element count.'
    suites = list(root.iter('testsuite'))
    assert suites, 'Missing testsuite.'
    if root.tag == 'testsuites' and any(key in root.attrib for key in ('tests', 'errors', 'failures', 'skipped')):
        suites.append(root)
    for suite in suites:
        counts = {
            'tests': len(list(suite.iter('testcase'))),
            'errors': 0,
            'failures': len(list(suite.iter('failure'))),
            'skipped': 0,
        }
        for field, count in counts.items():
            assert suite.attrib.get(field) == str(count), f'Wrong JUnit {field} count.'
    seen = set()
    failures = set()
    for case in root.iter('testcase'):
        key = (case.attrib['classname'], case.attrib['name'])
        assert key not in seen, f'Duplicate test: {key}'
        seen.add(key)
        assert case.find('error') is None, f'Setup/collection/runtime error: {key}'
        assert case.find('skipped') is None, f'Unexpected skip: {key}'
        found = case.findall('failure')
        assert len(found) <= 1, f'Multiple failures in {key}'
        if found:
            failures.add(key)
            assert key in expected_failures, f'Unexpected failing node: {key}'
            failure = found[0]
            assert set(failure.attrib) == {'message'}, f'Unexpected failure attributes: {key}'
            assert not list(failure), f'Nested failure content: {key}'
            assert not (failure.tail or '').strip(), f'Extra text after failure: {key}'
            actual = {
                'message': normalize_diagnostic(failure.attrib['message']),
                'text': normalize_diagnostic(failure.text),
            }
            assert actual == EXPECTED_FAILURES[key[1]], f'Unexpected full failure diagnostic: {key}'
    assert seen == expected, f'Wrong node set: missing={expected - seen}; extra={seen - expected}'
    assert failures == set(expected_failures), f'Wrong failed-node set: {failures}'
    return {'phase': phase, 'collected': len(seen), 'passed': len(seen) - len(failures), 'expected_failures': len(failures)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['baseline', 'candidate'])
    parser.add_argument('junit', type=Path)
    parser.add_argument('process_exit', type=int)
    parser.add_argument('guard_result', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.junit.read_text(), args.phase, args.process_exit, json.loads(args.guard_result.read_text())), indent=2))
