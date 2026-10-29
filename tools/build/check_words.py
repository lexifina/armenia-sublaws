"""Independent word check: ARLIS's own page against what git holds, for a sample of texts.

The source side is the raw cached page (.cache/text/<id>.html.gz): the text of its `a4` body with the act header and
title removed, read with lxml's text_content() and nothing from parse_text.py. The git side is every file of that
law at the commit whose `Text:` trailer names the text, read with git cat-file. Both are reduced to words (runs of
letters and digits, superscripts as digits) and compared as counts, so file order does not matter.

    python scripts/armenia-law/check_words.py ~/Documents/armenia-law [--sample 2000] [--seed 1]

Reports texts where source words are missing from git (dropped text) or git has words the source lacks (leaked
markup), worst first.
"""
import argparse
import csv
import gzip
import random
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import lxml.html as lh

import corpus_set  # `--set sublaws` checks lexifina/armenia-sublaws against its own cache

CACHE = Path(__file__).parent / ('.cache-sublaws' if corpus_set.SUBLAWS else '.cache') / 'text'
SUP = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹', '0123456789')
WORD = re.compile(r'[^\W_]+')
# Words the repo adds by design: our own markup words are none (headings are copied text), so nothing is excused.


def words(s: str) -> Counter:
    # Letters and digits only, with no word boundaries: the source splits words across elements (a drop letter in
    # its own span), so any word split would be the checker's artefact, not the repo's.
    return Counter(c for c in s.translate(SUP).lower() if c.isalnum())


def source_words(tid: str) -> Counter:
    doc = lh.fromstring(gzip.decompress((CACHE / f'{tid}.html.gz').read_bytes()).decode('utf-8', 'replace'))
    a4 = doc.find_class('a4')
    root = a4[0] if a4 else doc
    for junk in root.find_class('act-info') + root.find_class('act-title'):
        junk.getparent().remove(junk)
    for el in root.xpath('.//script|.//style|.//button'):
        el.getparent().remove(el)
    # Join every text node with a space: adjacent elements often have no whitespace between them.
    return words(' '.join(root.itertext()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('repo', type=Path)
    ap.add_argument('--sample', type=int, default=2000)
    ap.add_argument('--seed', type=int, default=1)
    args = ap.parse_args()
    repo = args.repo

    def git(*a: str) -> str:
        return subprocess.run(['git', '-c', 'core.quotepath=false', '-C', str(repo), *a], capture_output=True,
                              text=True, encoding='utf-8', check=True).stdout

    paths = {row['id']: row['path'].rstrip('/') for row in csv.DictReader(open(repo / 'laws.csv', encoding='utf-8'))}
    index: dict[str, tuple[str, str]] = {}
    last: dict[tuple[str, str], str] = {}
    for line in git('log', 'main', '--format=%H%x1f%(trailers:key=Text,valueonly,separator=%x1e)').splitlines():
        h, _, texts = line.partition('\x1f')
        for t in texts.split('\x1e'):
            m = re.match(r'\s*(\d+)\s*\(law (\d+)\)', t)
            # Only a commit whose LAST text for that law is this one has exactly this text in its tree.
            if m:
                last[(h, m.group(2))] = m.group(1)
    for (h, law), t in last.items():
        index.setdefault(t, (h, law))
    tids = sorted(index, key=int)
    random.Random(args.seed).shuffle(tids)
    tids = sorted(tids[:args.sample], key=int)
    print(f'{len(index)} texts named by commits; checking {len(tids)}', flush=True)

    cat = subprocess.Popen(['git', '-C', str(repo), 'cat-file', '--batch'], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE)

    def blob(spec: str) -> bytes:
        cat.stdin.write(spec.encode('utf-8') + b'\n')
        cat.stdin.flush()
        header = cat.stdout.readline().split()
        if header[1] == b'missing':
            return b''
        data = cat.stdout.read(int(header[2]))
        cat.stdout.read(1)
        return data

    results = []
    for tid in tids:
        commit, law = index[tid]
        folder = paths.get(law)
        if not folder or not (CACHE / f'{tid}.html.gz').exists():
            continue
        names = git('ls-tree', '-r', '--name-only', commit, folder + '/').split('\n')
        ours = Counter()
        for n in filter(None, names):
            ours += words(blob(f'{commit}:{n}').decode('utf-8', 'replace'))
        src = source_words(tid)
        missing = sum((src - ours).values())
        extra = sum((ours - src).values())
        total = sum(src.values()) or 1
        results.append((missing / total, tid, law, missing, extra, total, (src - ours).most_common(6),
                        (ours - src).most_common(6)))
    cat.stdin.close()

    results.sort(reverse=True)
    bad = [r for r in results if r[0] > 0.01 or r[4] > max(20, 0.01 * r[5])]
    words_src = sum(r[5] for r in results)
    words_missing = sum(r[3] for r in results)
    words_extra = sum(r[4] for r in results)
    print(f'checked {len(results)} texts, {words_src} source letters and digits: {words_missing} missing '
          f'({100 * words_missing / max(1, words_src):.3f}%), {words_extra} extra '
          f'({100 * words_extra / max(1, words_src):.3f}%); {len(bad)} texts over 1%')
    for r in bad[:25]:
        print(f'  text {r[1]} (law {r[2]}): missing {r[3]}/{r[5]}, extra {r[4]}; '
              f'missing e.g. {r[6]}; extra e.g. {r[7]}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
