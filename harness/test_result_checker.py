"""Exercise strict result checking without executing the project or a provider."""
import copy
import unittest
import xml.etree.ElementTree as ET

from check_results import BASELINE, CANDIDATE, EXPECTED_FAILURES, FAILURES, verify


def fixture(phase):
    root = ET.Element('testsuite')
    for module, name in sorted(BASELINE if phase == 'baseline' else CANDIDATE):
        case = ET.SubElement(root, 'testcase', classname=module, name=name)
        if phase == 'baseline' and (module, name) in FAILURES:
            expected = EXPECTED_FAILURES[name]
            ET.SubElement(case, 'failure', message=expected['message']).text = expected['text']
    root.attrib.update(tests=str(len(root)), errors='0', failures=str(len(FAILURES) if phase == 'baseline' else 0), skipped='0')
    return root


class StrictResultCheckerTests(unittest.TestCase):
    def setUp(self):
        self.guard = {'phase': 'baseline', 'guard_ok': True, 'unexpected_guard_events': [], 'pytest_exit': 1}
        self.root = fixture('baseline')

    def check(self, root=None, code=1, guard=None):
        return verify(ET.tostring(self.root if root is None else root, encoding='unicode'), 'baseline', code, self.guard if guard is None else guard)

    def test_exact_baseline_is_accepted(self):
        self.assertEqual(self.check(), {'phase': 'baseline', 'collected': 16, 'passed': 9, 'expected_failures': 7})

    def test_exact_candidate_is_accepted(self):
        guard = dict(self.guard, phase='candidate', pytest_exit=0)
        self.assertEqual(verify(ET.tostring(fixture('candidate'), encoding='unicode'), 'candidate', 0, guard)['passed'], 22)

    def test_rejects_setup_error(self):
        ET.SubElement(self.root[0], 'error', message='fixture setup failed')
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_wrong_failure_reason(self):
        next(self.root.iter('failure')).set('message', 'AssertionError: unrelated failure')
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_extra_failure(self):
        case = next(case for case in self.root if case.find('failure') is None)
        ET.SubElement(case, 'failure', message='AssertionError: unexpected')
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_missing_failure(self):
        case = next(case for case in self.root if case.find('failure') is not None)
        case.remove(case.find('failure'))
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_extra_node(self):
        ET.SubElement(self.root, 'testcase', classname='extra', name='test_extra')
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_missing_node(self):
        self.root.remove(self.root[0])
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_duplicate_node(self):
        self.root.append(copy.deepcopy(self.root[0]))
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_skip(self):
        ET.SubElement(self.root[0], 'skipped')
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_collection_exit(self):
        with self.assertRaises(AssertionError):
            self.check(code=2)

    def test_rejects_guard_failure(self):
        with self.assertRaises(AssertionError):
            self.check(guard=dict(self.guard, guard_ok=False))


    def test_rejects_appended_assertion_in_same_message(self):
        failure = next(self.root.iter('failure'))
        failure.set('message', failure.attrib['message'] + '\nAssertionError: unrelated hidden failure')
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_chained_exception_in_same_body(self):
        failure = next(self.root.iter('failure'))
        failure.text = ('AssertionError: UNRELATED_INDEPENDENT_ASSERTION\n\n'
                        'During handling of the above exception, another exception occurred:\n\n' + failure.text)
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_different_body_with_correct_message(self):
        next(self.root.iter('failure')).text = 'ValueError: unrelated setup problem'
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_appended_assertion_in_same_body(self):
        failure = next(self.root.iter('failure'))
        failure.text += '\nAssertionError: unrelated hidden failure'
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_multiple_failures_in_same_case(self):
        case = next(case for case in self.root if case.find('failure') is not None)
        case.append(copy.deepcopy(case.find('failure')))
        with self.assertRaises(AssertionError):
            self.check()

    def test_accepts_only_expected_monkeypatch_address_variation(self):
        for failure in self.root.iter('failure'):
            failure.text = failure.text.replace('object at ADDRESS>', 'object at 0xabcdef012345>')
        self.assertEqual(self.check()['expected_failures'], 7)

    def test_rejects_unrelated_address_text(self):
        next(self.root.iter('failure')).text += '\nother = <object at 0xabcdef012345>'
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_additional_failure_xml_child(self):
        ET.SubElement(next(self.root.iter('failure')), 'extra').text = 'AssertionError: unrelated'
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_extra_text_after_failure(self):
        next(self.root.iter('failure')).tail = 'AssertionError: unrelated'
        with self.assertRaises(AssertionError):
            self.check()



    def test_rejects_testsuite_error(self):
        ET.SubElement(self.root, 'error', message='Collection failed')
        with self.assertRaises(AssertionError):
            self.check()

    def test_rejects_wrong_suite_counts(self):
        for field in ('tests', 'errors', 'failures', 'skipped'):
            with self.subTest(field=field):
                bad = copy.deepcopy(self.root)
                bad.set(field, '99')
                with self.assertRaises(AssertionError):
                    self.check(root=bad)

    def test_rejects_wrong_failure_type(self):
        next(self.root.iter('failure')).set('type', 'RuntimeError')
        with self.assertRaises(AssertionError):
            self.check()


if __name__ == '__main__':
    unittest.main()
