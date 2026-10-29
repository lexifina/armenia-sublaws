"""README, REPRODUCE.md, LICENSE, laws.csv, corpus.json, data/ and tools/ for the Armenian law repository."""
import csv
import hashlib
import io
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import corpus_set

HERE = Path(__file__).parent
REPO_FILES = HERE / ('repo-sublaws' if corpus_set.SUBLAWS else 'repo')
CACHE = HERE / ('.cache-sublaws' if corpus_set.SUBLAWS else '.cache')
SCRIPTS = ('fetch.py', 'parse_text.py', 'build.py', 'docs.py') + (('corpus_set.py', 'check_words.py')
                                                                   if corpus_set.SUBLAWS else ())


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def text_sums() -> str:
    out = []
    for p in sorted((CACHE / 'text').glob('*.html.gz'), key=lambda p: int(p.name.split('.')[0])):
        out.append(f"{p.name.split('.')[0]}\t{_sha(p.read_bytes())}\n")
    return ''.join(out)


def render(laws: list[dict], commits: list[dict], issues: list[dict], missing: list[dict], today: str) -> dict[str, bytes]:
    from build import TYPE_DIR, TYPE_NAME, act_name
    main = [c for c in commits if not c['future']]
    future = [c for c in commits if c['future']]
    kinds = Counter(c['kind'] for c in main)
    types = Counter(l['type'] for l in laws)
    texts = sum(len(l['versions']) for l in laws)
    first = min(c['date'] for c in main) if main else ''
    last = max(c['date'] for c in main) if main else ''
    from build import act_key
    authors = {act_key(c['act']) for c in main if c['kind'] == 'amendment'}
    ev = Counter(e for c in main if c['kind'] == 'amendment' for p in c['parts'] for e in p['evidence'].values())
    retro = sum(1 for c in main if c['kind'] == 'amendment' and c['act'].get('date') and c['date'] < c['act']['date'])

    out = io.StringIO()
    w = csv.writer(out, lineterminator='\n')
    w.writerow(['id', 'type', 'title', 'number', 'enacted', 'in_force', 'status', 'texts', 'path', 'source'])
    for l in laws:
        w.writerow([l['id'], TYPE_NAME.get(l['type'], ''), l['title'], l['number'], l['enacted'] or '',
                    l['effective'] or '', l['status'], len(l['versions']), f"{l['dir']}/",
                    f"https://www.arlis.am/hy/acts/{l['id']}"])
    laws_csv = out.getvalue()

    iss = io.StringIO()
    w = csv.writer(iss, lineterminator='\n')
    w.writerow(['law', 'text', 'issue'])
    for i in sorted(issues, key=lambda i: (i['law'], i['text'])):
        w.writerow([i['law'], i['text'], i['issue']])
    mis = io.StringIO()
    w = csv.writer(mis, lineterminator='\n')
    w.writerow(['law', 'amending_act', 'act_date', 'act_id'])
    for m in sorted(missing, key=lambda m: (m['law'], m['act_date'], m['act'])):
        w.writerow([m['law'], m['act'], m['act_date'], m['act_id']])

    stats = {
        'today': today, 'laws': len(laws), 'constitutions': types[1], 'codes': types[5], 'laws_ordinary': types[7],
        'texts': texts, 'commits': len(main) + 1, 'future_commits': len(future), 'original': kinds['original'],
        'amendment': kinds['amendment'], 'unexplained': kinds['unexplained'], 'amending_acts': len(authors),
        'first': first, 'last': last, 'unreadable': len(issues), 'not_incorporated': len(missing),
        'retroactive': retro, 'evidence_note': ev['note'], 'evidence_edition': ev['edition'],
        'evidence_caught_up': ev['note (no text of its own)'],
    }
    if corpus_set.SUBLAWS:
        stats.update({'government': types['government'], 'prime_minister': types['prime-minister'],
                      'ministerial': types['ministerial'], 'acts': len(laws)})
        # The README's example: the government decision with the most texts.
        gov = [l for l in laws if l['type'] == 'government'] or laws
        stats['example_id'] = max(gov, key=lambda l: (len(l['versions']), -l['id']))['id'] if gov else ''
        for k in ('constitutions', 'codes', 'laws_ordinary'):
            stats.pop(k)
    sums = text_sums()
    stats['texts_sha256'] = _sha(sums.encode())
    tool_versions = {
        'python': sys.version.split()[0],
        'git': subprocess.run(['git', '--version'], capture_output=True, text=True).stdout.strip(),
        'curl': subprocess.run(['curl', '--version'], capture_output=True, text=True).stdout.split('\n')[0],
        'lxml': __import__('lxml').__version__,
    }

    def fill(t: str) -> str:
        for k, v in stats.items():
            t = t.replace('{{' + k.upper() + '}}', str(v))
        for name in SCRIPTS:
            t = t.replace('{{SHA_' + name.upper().replace('.', '_') + '}}', _sha((HERE / name).read_bytes()))
        for k, v in tool_versions.items():
            t = t.replace('{{V_' + k.upper() + '}}', v)
        return t

    corpus = {
        'corpus': 'am/national/acts',
        'name': 'Laws of the Republic of Armenia (Constitution, codes and laws)',
        'label': 'Armenia',
        'language': 'hy',
        'history_from': first,
        'record_to': last,
        'record_note': f'{len(laws)} acts on ARLIS ({types[1]} constitutions, {types[5]} codes, {types[7]} laws), '
                       f'every consolidated text, to the in-force date of {last}; data built {today}.',
        'in_force_trailer': 'In-force',
        'has_future_branch': True,
        'future_branch': 'future',
        'laws': {'constitution': types[1], 'codes': types[5], 'laws': types[7]},
        'built': today,
        'dates': {'commit': 'in-force (start of the period ARLIS gives each consolidated text)',
                  'other_trailers': ['Enacted'], 'time': '12:00 Asia/Yerevan (+0400)',
                  'before_1970': 'clamped to 1970-01-01', 'future': 'branch future, never merged'},
        'author': {'amendment': 'the amending act (ARLIS pairs each consolidated text with one act)',
                   'original': 'the law itself', 'evidence_trailer': 'Evidence'},
        'scope': {
            'trailer': 'Applies',
            'groups': 'any one line',
            'conditions': 'all of a line',
            'when_absent': 'not extracted for Armenia yet; transitional provisions are in the amending act at the '
                           'Source link',
            'default_reach': {
                'rule': 'no retroactive effect unless the act says so, and never to worsen a person\'s position',
                'meaning': 'a legal act applies to relations that arise after it takes effect; it has retroactive '
                           'force only where the act provides for it, and acts that establish or aggravate liability '
                           'or worsen a person\'s legal position have no retroactive force',
                'authority': 'Constitution of the Republic of Armenia (2015), article 73; Law on Normative Legal '
                             'Acts (ՀՕ-180-Ն, 2018), article 28; on transitional provisions, article 13(6)',
                'decided_here': False,
            },
        },
        'citation': {'file': r'((?:constitution|code|law)/[0-9]+)/0*([0-9]+(?:\.[0-9]+)?)\.md',
                     'cites': r'(^|[^0-9.]){n}(-րդ)? հոդված'},
        'tool': 'tools/in_force_on.py',
    }

    if corpus_set.SUBLAWS:
        corpus.update({
            'corpus': 'am/national/sublaws',
            'name': 'Normative sub-laws of the Republic of Armenia (government and prime-minister decisions, '
                    'ministerial orders)',
            'label': 'Armenia (sub-laws)',
            'record_note': f"{len(laws)} normative acts on ARLIS ({types['government']} government decisions, "
                           f"{types['prime-minister']} prime-minister decisions, {types['ministerial']} ministerial "
                           f"orders), every consolidated text, to the in-force date of {last}; data built {today}.",
            'laws': {'government_decisions': types['government'], 'prime_minister_decisions': types['prime-minister'],
                     'ministerial_orders': types['ministerial']},
            'companion': 'lexifina/armenia-law (am/national/acts): the Constitution, codes and laws',
        })
        corpus['author']['original'] = 'the act itself'
        corpus['scope']['default_reach']['authority'] = (
            'Constitution of the Republic of Armenia (2015), article 73; Law on Normative Legal Acts (ՀՕ-180-Ն, '
            '2018), article 28, which covers every normative legal act, sub-laws included; on transitional '
            'provisions, article 13(6)')
        corpus['citation'] = {'file': r'((?:government|prime-minister|ministerial)/[0-9]+)/0*([0-9]+(?:\.[0-9]+)?)\.md',
                              'cites': r'(^|[^0-9.]){n}(-րդ)? հոդված'}
    files = {
        'corpus.json': (json.dumps(corpus, indent=2, ensure_ascii=False) + '\n').encode('utf-8'),
        'README.md': fill((REPO_FILES / 'README.md').read_text('utf-8')).encode('utf-8'),
        'REPRODUCE.md': fill((REPO_FILES / 'REPRODUCE.md').read_text('utf-8')).encode('utf-8'),
        'LICENSE': (REPO_FILES / 'LICENSE').read_bytes(),
        'laws.csv': laws_csv.encode('utf-8'),
        'data/unreadable.csv': iss.getvalue().encode('utf-8'),
        'data/not-incorporated.csv': mis.getvalue().encode('utf-8'),
        'data/stats.json': (json.dumps(stats, indent=1, sort_keys=True) + '\n').encode('utf-8'),
        'data/texts-sha256.tsv': sums.encode('utf-8'),
        'tools/in_force_on.py': (REPO_FILES / 'tools' / 'in_force_on.py').read_bytes(),
    }
    for name in SCRIPTS:
        files[f'tools/build/{name}'] = (HERE / name).read_bytes()
    for name in ('README.md', 'REPRODUCE.md', 'LICENSE', 'tools/in_force_on.py'):
        files[f'tools/build/repo/{name}'] = (REPO_FILES / name).read_bytes()
    return files
