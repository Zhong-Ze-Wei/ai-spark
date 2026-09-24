#!/usr/bin/env python3
"""Check migrated content against the preserved edition and all local links."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import re

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'content/build-manifest.json').read_text())
data = json.loads((ROOT / 'content/data.json').read_text())
archive = (ROOT / 'archive.html').read_text()
original = json.loads(re.search(r'<script[^>]*id="preserved-v1-data"[^>]*>(.*?)</script>', archive, re.S)[1])
assert data == original, 'The preserved data differs from the existing edition.'
expected = {'topics':38,'debates':20,'events':28,'people':26,'sources':177,'tasks':9,'methods':10,'questions':12,'glossary':25,'routes':4}
assert manifest['counts'] == expected
assert len(json.loads((ROOT / 'content/editedTopics.json').read_text())) == 38


class Document(HTMLParser):
    def __init__(self, content):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.h1 = 0
        self.quote = None
        self.quotes = []
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, f'Duplicate id {a["id"]}'
            self.ids.add(a['id'])
        if tag == 'h1':
            self.h1 += 1
        if tag == 'blockquote':
            self.quote = ''
        if tag in ('a','link','img','script'):
            link = a.get('href') or a.get('src')
            if link:
                self.links.append(link)

    def handle_data(self, value):
        if self.quote is not None:
            self.quote += value

    def handle_endtag(self, tag):
        if tag == 'blockquote' and self.quote is not None:
            self.quotes.append(self.quote)
            self.quote = None


parsed = {ROOT / p: Document((ROOT / p).read_text()) for p in manifest['pages']}
broken = []
link_count = 0
for path, doc in parsed.items():
    assert doc.h1 == 1, (str(path.relative_to(ROOT)), doc.h1)
    for link in doc.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        link_count += 1
        target = (path.parent / unquote(url.path)).resolve() if url.path else path
        if target.is_dir():
            target /= 'index.html'
        if not target.exists():
            broken.append((str(path.relative_to(ROOT)), link))
        elif url.fragment and target in parsed and unquote(url.fragment) not in parsed[target].ids:
            broken.append((str(path.relative_to(ROOT)), link, 'missing anchor'))
for s in data['sources']:
    p = ROOT / 'sources' / s['id'] / 'index.html'
    assert parsed[p].quotes == [s['text']], 'Original quote changed: ' + s['id']
assert not broken, json.dumps(broken, ensure_ascii=False, indent=2)
assert '最后更好的答案' not in (ROOT / 'topics/t16/index.html').read_text()
assert '很晚才被明确分开' not in (ROOT / 'topics/t19/index.html').read_text()
print(f'PASS: {len(parsed)} pages, {link_count} local links, all 177 quotes identical, all archive records preserved.')
