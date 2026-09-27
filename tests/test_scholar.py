import importlib.util
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


if __name__ == '__main__':
    unittest.main()
