"""Conversor mínimo de Markdown para HTML (o subconjunto usado nos manuais)."""
import html
import re


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t


def table(rows):
    rows = [r.strip().strip('|').split('|') for r in rows if not re.match(r'^\s*\|\s*-', r)]
    out = ['<table>', '<thead><tr>' + ''.join(f'<th>{inline(c.strip())}</th>' for c in rows[0]) + '</tr></thead><tbody>']
    for r in rows[1:]:
        out.append('<tr>' + ''.join(f'<td>{inline(c.strip())}</td>' for c in r) + '</tr>')
    out.append('</tbody></table>')
    return '\n'.join(out)


def convert(md):
    lines = md.split('\n')
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        s = l.strip()
        if not s:
            i += 1
            continue
        m = re.match(r'^(#{1,3}) (.*)', l)
        if m:
            n = len(m.group(1))
            out.append(f'<h{n}>{inline(m.group(2))}</h{n}>')
            i += 1
            continue
        if s.startswith('```'):
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append('<pre>' + '\n'.join(code) + '</pre>')
            continue
        if s.startswith('|'):
            t = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                t.append(lines[i])
                i += 1
            out.append(table(t))
            continue
        if s.startswith('>'):
            t = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                t.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f'<blockquote>{inline(" ".join(t))}</blockquote>')
            continue
        if re.match(r'^(\d+)\. |^- ', l):
            ordered = bool(re.match(r'^\d+\. ', l))
            tag = 'ol' if ordered else 'ul'
            items = []
            while i < len(lines):
                cur = lines[i]
                if re.match(r'^(\d+\. |- )', cur):
                    items.append([re.sub(r'^(\d+\. |- )', '', cur), []])
                    i += 1
                elif cur.startswith('   ') and items and cur.strip():
                    items[-1][1].append(cur[3:])
                    i += 1
                elif not cur.strip() and i + 1 < len(lines) and (lines[i + 1].startswith('   ') or re.match(r'^(\d+\. |- )', lines[i + 1])):
                    i += 1
                else:
                    break
            parts = [f'<{tag}>']
            for head, sub in items:
                inner = convert('\n'.join(sub)) if sub else ''
                parts.append(f'<li>{inline(head)}{inner}</li>')
            parts.append(f'</{tag}>')
            out.append('\n'.join(parts))
            continue
        para = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||>|- |\d+\. |```)', lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(f'<p>{inline(" ".join(para))}</p>')
    return '\n'.join(out)
