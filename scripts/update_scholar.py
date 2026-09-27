#!/usr/bin/env python3
"""Fetch public all-time Scholar metrics; never replace verified data on failure."""
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

SCHOLAR_ID = 'QkURxEAAAAAJ'
SOURCE = f'https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en'


class MetricsTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.cell = None
        self.row = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'table' and attrs.get('id') == 'gsc_rsb_st':
            self.in_table = True
        if not self.in_table:
            return
        if tag == 'tr':
            self.row = []
        if tag in ('td', 'th'):
            self.cell = []

    def handle_data(self, data):
        if self.in_table and self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if not self.in_table:
            return
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(''.join(self.cell).strip())
            self.cell = None
        if tag == 'tr':
            self.rows.append(self.row)
        if tag == 'table':
            self.in_table = False


def parse_metrics(html):
    table = MetricsTable()
    table.feed(html)
    rows = {row[0].casefold(): row[1:] for row in table.rows if row}
    result = {}
    for label, key in [('citations', 'citations'), ('h-index', 'h_index')]:
        values = rows.get(label, [])
        if not values or not re.fullmatch(r'[0-9][0-9,\s]*', values[0]):
            raise ValueError(f'Missing or invalid all-time {label}; Scholar may have blocked the request.')
        result[key] = int(re.sub(r'[,\s]', '', values[0]))
    if result['h_index'] ** 2 > result['citations']:
        raise ValueError('Inconsistent metrics; refusing to replace the last verified values.')
    return result


def refresh(output):
    request = Request(SOURCE, headers={'User-Agent': 'Mozilla/5.0 (compatible; AcademicProfileMetrics/1.0)', 'Accept-Language': 'en-US,en;q=0.9'})
    with urlopen(request, timeout=30) as response:
        html = response.read(2_000_000).decode('utf-8')
    metrics = parse_metrics(html)
    data = {'scholar_id': SCHOLAR_ID, 'source': SOURCE, **metrics,
            'checked_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    temporary.replace(output)
    print(f"Verified {metrics['citations']} citations, h-index {metrics['h_index']}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'assets/data/scholar.json')
    args = parser.parse_args()
    try:
        refresh(args.output)
    except Exception as error:
        print(f'Scholar refresh failed; existing data preserved: {error}', file=sys.stderr)
        sys.exit(1)
