import importlib.util
import io
import json
import os
from urllib.error import HTTPError, URLError
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('scholar', Path(__file__).resolve().parents[1] / 'scripts/update_scholar.py')
scholar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scholar)


def table(citations='1,234', h='12'):
    return f'''<div>99999</div><table id="gsc_rsb_st"><tr><th></th><th>All</th><th>Since 2021</th></tr>
    <tr><td><a>Citations</a></td><td>{citations}</td><td>45</td></tr>
    <tr><td><a>h-index</a></td><td>{h}</td><td>3</td></tr></table>'''


class ScholarTests(unittest.TestCase):
    def test_all_time_column_and_formatted_numbers(self):
        self.assertEqual(scholar.parse_metrics(table()), {'citations': 1234, 'h_index': 12})

    def test_blocked_page_is_not_zero(self):
        with self.assertRaises(ValueError):
            scholar.parse_metrics('<html>Please complete a CAPTCHA</html>')

    def test_missing_and_inconsistent_values_rejected(self):
        for citations, h in [('-', '8'), ('10', '8'), ('342', '')]:
            with self.subTest(citations=citations, h=h), self.assertRaises(ValueError):
                scholar.parse_metrics(table(citations, h))

    def test_valid_zero(self):
        self.assertEqual(scholar.parse_metrics(table('0', '0')), {'citations': 0, 'h_index': 0})

    def test_failed_request_preserves_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'scholar.json'
            output.write_text('{"citations":342,"h_index":8}')
            with patch.object(scholar, 'urlopen', side_effect=OSError('rate limited')):
                with self.assertRaises(OSError):
                    scholar.refresh(output)
            self.assertEqual(output.read_text(), '{"citations":342,"h_index":8}')

    def test_temporary_failure_recovers(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'scholar.json'
            with patch.object(scholar, 'urlopen', side_effect=[URLError('connection reset'), io.BytesIO(table().encode())]) as fetch, patch.object(scholar.time, 'sleep') as sleep:
                scholar.refresh(output)
            self.assertEqual(fetch.call_count, 2)
            sleep.assert_called_once_with(15)
            self.assertEqual(json.loads(output.read_text())['citations'], 1234)

    def test_retry_policy_preserves_snapshot(self):
        for code, headers, attempts, delays in [
            (403, {}, 1, []),
            (429, {}, 3, [15, 30]),
            (503, {'Retry-After': '45'}, 3, [45, 45]),
            (429, {'Retry-After': '3600'}, 1, []),
            (503, {'Retry-After': 'Wed, 01 Jan 2099 00:00:00 GMT'}, 1, []),
        ]:
            with self.subTest(code=code, headers=headers), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'scholar.json'
                original = '{"citations":350,"h_index":8}'
                output.write_text(original)
                error = HTTPError(scholar.SOURCE, code, 'upstream error', headers, None)
                with patch.object(scholar, 'urlopen', side_effect=error) as fetch, patch.object(scholar.time, 'sleep') as sleep:
                    with self.assertRaises(HTTPError):
                        scholar.refresh(output)
                self.assertEqual(fetch.call_count, attempts)
                self.assertEqual([call.args[0] for call in sleep.call_args_list], delays)
                self.assertEqual(output.read_text(), original)

    def test_captcha_is_not_retried_or_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'scholar.json'
            output.write_text('original')
            with patch.object(scholar, 'urlopen', return_value=io.BytesIO(b'Please complete a CAPTCHA')) as fetch, patch.object(scholar.time, 'sleep') as sleep:
                with self.assertRaises(ValueError):
                    scholar.refresh(output)
            self.assertEqual(fetch.call_count, 1)
            sleep.assert_not_called()
            self.assertEqual(output.read_text(), 'original')

    def test_failure_annotation_escapes_workflow_commands(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'}), patch('sys.stdout', new_callable=io.StringIO) as stdout:
            scholar.report_failure(ValueError('bad%value\n::notice::injected'))
        self.assertIn('bad%25value%0A::notice::injected', stdout.getvalue())
        self.assertEqual(len(stdout.getvalue().splitlines()), 1)


if __name__ == '__main__':
    unittest.main()
