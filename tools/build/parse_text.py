"""Read one ARLIS print view (`/hy/acts/<id>/print/act`) into its header and units.

    parse(html: str) -> {'info': {label: value}, 'title': str, 'units': [{'id', 'kind', 'heading': [..], 'lines': [..]}]}

The text is the publisher's own HTML: one <P> per paragraph, article headings in a two-cell table
(`Հոդված 15.` | title), chapter and part headings as centred paragraphs, appendices (`Հավելված N`) at the end.
Units: `title` (everything before the first article), one per article, one per appendix. Each <P> is one line,
so `git blame` works paragraph by paragraph (an article's parts are paragraphs). A table row is one line, its
cells joined by ` | `. Superscripts are kept as Unicode superscript digits (`327¹`); in file names they become
`327.1`, the form ARLIS uses in newer texts, so a renumbering of notation alone does not move a file.
"""
import re

from lxml import html as lh

SPACE = re.compile(r'[\s ​]+')
SUP = str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')
UNSUP = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹', '0123456789')
# Article headings are sometimes in capitals ("ՀՈԴՎԱԾ 58."), so match case-insensitively.
ARTICLE = re.compile(r'^Հոդված\s*([0-9][0-9.,⁰¹²³⁴⁵⁶⁷⁸⁹\s-]*?)\s*[.:]?\s*$', re.I)
ARTICLE_INLINE = re.compile(r'^Հոդված\s*([0-9][0-9.⁰¹²³⁴⁵⁶⁷⁸⁹-]*?)\s*[.:](?:\s+(.*))?$', re.I)
ANNEX = re.compile(r'^(?:Հավելված|ՀԱՎԵԼՎԱԾ)\s*(?:թիվ\s*|N\s*)?([0-9]+[0-9.⁰¹²³⁴⁵⁶⁷⁸⁹-]*)?\s*$', re.I)


def inline_text(el) -> str:
    """Text of an element, nested tables excluded, superscripts as superscript digits."""
    out: list[str] = []

    def walk(e, sup=False):
        if not isinstance(e.tag, str):
            if e.tail:
                out.append(e.tail.translate(SUP) if sup else e.tail)
            return
        tag = e.tag.lower()
        if tag in ('table', 'script', 'style'):
            if e.tail:
                out.append(e.tail.translate(SUP) if sup else e.tail)
            return
        inner_sup = sup or tag == 'sup'
        if tag == 'br':
            out.append(' ')
        if e.text:
            out.append(e.text.translate(SUP) if inner_sup else e.text)
        for c in e:
            walk(c, inner_sup)
        if e.tail:
            out.append(e.tail.translate(SUP) if sup else e.tail)

    if el.text:
        out.append(el.text.translate(SUP) if el.tag.lower() == 'sup' else el.text)
    for c in el:
        walk(c, el.tag.lower() == 'sup')
    # ⚖ is ARLIS's link to case law on the article, not part of the law.
    return SPACE.sub(' ', ''.join(out).replace('⚖', ' ')).strip()


def blocks(root):
    """Yield ('p', text, centred) and ('table', rows) in document order."""
    for e in root:
        if not isinstance(e.tag, str):
            continue
        tag = e.tag.lower()
        if tag in ('script', 'style'):
            continue
        if tag == 'table':
            rows = []
            for tr in e.iter('tr', 'TR'):
                cells = [inline_text(td) for td in tr if isinstance(td.tag, str) and td.tag.lower() in ('td', 'th')]
                cells = [c for c in cells if c]
                if cells:
                    rows.append(cells)
            yield ('table', rows)
            continue
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'):
            t = inline_text(e)
            style = (e.get('style') or '').lower()
            centred = (e.get('align') or '').lower() == 'center' or 'text-align: center' in style
            if t:
                yield ('p', t, centred)
            # a table inside a paragraph (the publisher nests them)
            # (directly, or inside <STRONG>/<FONT>); tables inside those tables are read with them.
            for sub in e.iter():
                if sub is e or not isinstance(sub.tag, str) or sub.tag.lower() != 'table':
                    continue
                anc = sub.getparent()
                while anc is not None and anc is not e and not (isinstance(anc.tag, str) and anc.tag.lower() == 'table'):
                    anc = anc.getparent()
                if anc is e:
                    yield from blocks([sub])
            continue
        if tag in ('div', 'span', 'font', 'strong', 'b', 'em', 'i', 'center', 'tbody', 'blockquote', 'ul', 'ol'):
            if tag in ('span', 'font', 'strong', 'b', 'em', 'i') and not any(
                    isinstance(c.tag, str) and c.tag.lower() in ('p', 'table', 'div') for c in e.iter()):
                t = inline_text(e)
                if t:
                    yield ('p', t, False)
                continue
            if e.text and e.text.strip():
                yield ('p', SPACE.sub(' ', e.text).strip(), False)
            yield from blocks(e)
            if e.tail and e.tail.strip():
                yield ('p', SPACE.sub(' ', e.tail).strip(), False)
            continue
        t = inline_text(e)
        if t:
            yield ('p', t, False)




def file_id(num: str) -> str:
    n = num.strip().rstrip('.').replace(' ', '')
    n = re.sub(r'([⁰¹²³⁴⁵⁶⁷⁸⁹]+)', lambda m: '.' + m.group(1).translate(UNSUP), n)
    return re.sub(r'[^0-9A-Za-z.-]', '-', n).strip('-.') or 'x'


def parse(page: str) -> dict:
    doc = lh.fromstring(page)
    info = {}
    for row in doc.find_class('info-row'):
        cells = [SPACE.sub(' ', c.text_content()).strip() for c in row if isinstance(c.tag, str)]
        if len(cells) == 2:
            info[cells[0]] = cells[1]
    title_el = doc.find_class('act-title')
    title = SPACE.sub(' ', title_el[0].text_content()).strip() if title_el else ''
    a4 = doc.find_class('a4')
    root = a4[0] if a4 else doc
    for junk in root.find_class('act-info') + root.find_class('act-title'):
        junk.getparent().remove(junk)

    units: list[dict] = []
    front: list[str] = []
    pending: list[str] = []   # centred headings waiting for the next article
    cur: dict | None = None

    def new_unit(uid: str, kind: str, first: str, title_line: str = ''):
        nonlocal cur, pending
        base, n = uid, 1
        while any(u['id'] == uid for u in units):
            n += 1
            uid = f'{base}~{n}'
        cur = {'id': uid, 'kind': kind, 'heading': pending, 'lines': [], 'title': first, 'name': title_line}
        units.append(cur)
        pending = []

    def add(line: str, centred: bool = False):
        if cur is None:
            front.append(line)
        elif centred and cur['kind'] == 'article' and not cur['lines'] == []:
            pending.append(line)
        else:
            if pending:
                cur['lines'].extend(pending)
                pending.clear()
            cur['lines'].append(line)

    for b in blocks(root):
        if b[0] == 'table':
            rows = b[1]
            if rows and len(rows[0]) >= 1 and ARTICLE.match(rows[0][0]):
                m = ARTICLE.match(rows[0][0])
                name = ' '.join(rows[0][1:])
                new_unit(file_id(m.group(1)), 'article', f'Հոդված {m.group(1).strip()}.', name)
                for r in rows[1:]:
                    add(' | '.join(r))
                continue
            for r in rows:
                add(' | '.join(r))
            continue
        _, t, centred = b
        m = ARTICLE_INLINE.match(t)
        if m and len(t) < 400:
            new_unit(file_id(m.group(1)), 'article', f'Հոդված {m.group(1).strip()}.', m.group(2) or '')
            continue
        m = ANNEX.match(t)
        if m and (cur is not None):
            new_unit('annex-' + file_id(m.group(1) or '1'), 'annex', t)
            continue
        add(t, centred)
    if pending and cur is not None:
        cur['lines'].extend(pending)
    return {'info': info, 'title': title, 'front': front, 'units': units}


def armenian_share(d: dict) -> float:
    sample = ' '.join(d['front'][:20] + [l for u in d['units'][:20] for l in u['lines'][:3]])[:8000]
    letters = [c for c in sample if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if 'Ա' <= c <= '֏') / len(letters)
