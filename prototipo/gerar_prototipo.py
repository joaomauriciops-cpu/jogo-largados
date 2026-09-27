"""Gera o Manual de Prototipagem (kit para imprimir e recortar) em PDF.

    python3 gerar_prototipo.py

Saída: manual/Manual_de_Prototipagem_Largados_e_Pelados_0.5.pdf
"""
import glob
import html
import os
import subprocess

import dados as D

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
OUT_HTML = os.path.join(AQUI, 'prototipo_0.5.html')
OUT_PDF = os.path.join(RAIZ, 'manual', 'Manual_de_Prototipagem_Largados_e_Pelados_0.5.pdf')

e = lambda s: html.escape(s, quote=False)

# ----------------------------------------------------------------- ícones
ICON = {
    'comida': '<svg viewBox="0 0 24 24"><circle cx="12" cy="14" r="8" fill="#d9472b" stroke="#7a1f10" stroke-width="1.2"/>'
              '<path d="M12 6 C12 3 14 2 16 2" stroke="#5a3a1a" stroke-width="1.6" fill="none"/>'
              '<path d="M13 5 C16 3 19 5 18 7 C15 8 13 7 13 5Z" fill="#4c9a3f"/></svg>',
    'agua': '<svg viewBox="0 0 24 24"><path d="M12 2 C12 2 4.5 10.5 4.5 15 a7.5 7.5 0 0 0 15 0 C19.5 10.5 12 2 12 2Z" '
            'fill="#3a8fd6" stroke="#174d7a" stroke-width="1.2"/><path d="M8.5 15 a3.5 3.5 0 0 0 3 3.4" stroke="#cfe8fb" '
            'stroke-width="1.4" fill="none"/></svg>',
    'madeira': '<svg viewBox="0 0 24 24"><rect x="2" y="7" width="18" height="10" rx="2" fill="#8a5a2b" stroke="#4a2e12" '
               'stroke-width="1.2"/><ellipse cx="19" cy="12" rx="3" ry="5" fill="#d9ad73" stroke="#4a2e12" stroke-width="1.2"/>'
               '<ellipse cx="19" cy="12" rx="1.3" ry="2.3" fill="none" stroke="#8a5a2b" stroke-width=".9"/></svg>',
    'risco': '<svg viewBox="0 0 24 24"><path d="M12 2 L23 21 H1 Z" fill="#f2c230" stroke="#6b4e00" stroke-width="1.4" '
             'stroke-linejoin="round"/><rect x="11" y="8" width="2" height="7" fill="#3a2a00"/><circle cx="12" cy="18" r="1.3" fill="#3a2a00"/></svg>',
    'fogo': '<svg viewBox="0 0 24 24"><path d="M12 2 C14 7 19 9 19 15 a7 7 0 0 1 -14 0 C5 11 8 9 9 6 C10 9 11 10 12 10 C12 7 11 5 12 2Z" '
            'fill="#f07a1a" stroke="#8a3200" stroke-width="1.1"/><path d="M12 12 C13.5 14 15 15 15 17 a3 3 0 0 1 -6 0 C9 15.5 11 14 12 12Z" fill="#ffd34d"/></svg>',
    'abrigo': '<svg viewBox="0 0 24 24"><path d="M2 20 L12 4 L22 20 Z" fill="#b8874a" stroke="#4a2e12" stroke-width="1.3" '
              'stroke-linejoin="round"/><path d="M9.5 20 L12 15.5 L14.5 20 Z" fill="#3a2410"/></svg>',
    'check': '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#fff" stroke="#555" stroke-width="1.4"/>'
             '<path d="M7 12.5 L10.5 16 L17 8.5" stroke="#2e5e4e" stroke-width="2.4" fill="none" stroke-linecap="round"/></svg>',
    'resgate': '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#fff" stroke="#c8362f" stroke-width="2"/>'
               '<text x="12" y="16.5" font-size="12" font-weight="700" text-anchor="middle" fill="#c8362f" font-family="DejaVu Sans">H</text></svg>',
}


def icon(name, size='6mm'):
    return f'<span class="ic" style="width:{size};height:{size}">{ICON[name]}</span>'


# ------------------------------------------------------------------ CSS
CSS = """
@page { size: A4; margin: 8mm;
  @bottom-center { content: "Largados e Pelados 0.5 · Manual de prototipagem · pág. " counter(page); font: 6.5pt 'DejaVu Sans'; color: #999; } }
@page land { size: A4 landscape; margin: 8mm;
  @bottom-center { content: "Largados e Pelados 0.5 · Manual de prototipagem · pág. " counter(page); font: 6.5pt 'DejaVu Sans'; color: #999; } }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'DejaVu Sans', 'Liberation Sans', sans-serif; color: #22241f; }
.sheet { width: 194mm; height: 280mm; position: relative; break-after: page; overflow: hidden; }
.sheet.land { page: land; width: 281mm; height: 193mm; }
.sheet:last-child { break-after: auto; }
.ic { display: inline-block; vertical-align: middle; }
.ic svg { width: 100%; height: 100%; display: block; }
.label { position: absolute; top: 0; left: 0; right: 0; font-size: 7pt; color: #888; text-align: center; letter-spacing: .06em; }
/* texto do guia */
.doc { padding: 6mm 8mm; font-size: 9.2pt; line-height: 1.42; }
.doc h1 { font-size: 26pt; color: #2e5e4e; margin: 18mm 0 3mm; line-height: 1.1; }
.doc h2 { font-size: 13pt; color: #2e5e4e; border-bottom: 1.4pt solid #c8913b; padding-bottom: 1.2mm; margin: 5mm 0 2.5mm; }
.doc h3 { font-size: 10.5pt; color: #8a5a1c; margin: 3.5mm 0 1.5mm; }
.doc p { margin: 0 0 2mm; }
.doc ul, .doc ol { margin: 0 0 2mm; padding-left: 5.5mm; }
.doc li { margin-bottom: .8mm; }
.doc table { width: 100%; border-collapse: collapse; font-size: 8.2pt; margin: 1mm 0 3mm; }
.doc th { background: #2e5e4e; color: #fff; text-align: left; padding: 1.2mm 1.8mm; }
.doc td { border-bottom: .4pt solid #cfd6cf; padding: 1.1mm 1.8mm; vertical-align: top; }
.doc tbody tr:nth-child(even) td { background: #f2f5f3; }
.sub { font-size: 11pt; color: #8a5a1c; }
.box { background: #fbf5ea; border-left: 3pt solid #c8913b; padding: 2.5mm 4mm; margin: 2mm 0 3mm; }
/* grade de cartas: 3 x 3 de 63 x 88 mm */
.cards { position: absolute; left: 2.5mm; top: 6mm; display: grid; grid-template-columns: repeat(3, 63mm); grid-auto-rows: 88mm; }
.card { width: 63mm; height: 88mm; border: .25mm dashed #9a9a9a; position: relative; overflow: hidden; }
.cin { position: absolute; inset: 2.2mm; border-radius: 3mm; display: flex; flex-direction: column; overflow: hidden; }
.chead { color: #fff; padding: 1.6mm 2.5mm 1.4mm; font-size: 6.4pt; font-weight: 700; letter-spacing: .1em; display: flex; justify-content: space-between; }
.ctitle { font-size: 11pt; font-weight: 700; padding: 2mm 2.5mm 1mm; line-height: 1.15; }
.ctime { margin: 0 2.5mm 1.5mm; font-size: 6.4pt; font-weight: 700; border-radius: 1.5mm; padding: .7mm 1.8mm; align-self: flex-start; letter-spacing: .04em; }
.ctext { font-size: 7.6pt; line-height: 1.33; padding: 0 2.5mm; flex: 1; }
.cflav { font-family: 'DejaVu Serif', serif; font-style: italic; font-size: 6.6pt; color: #555; padding: 1mm 2.5mm 1.2mm; border-top: .3mm solid #ddd; margin: 0 1mm; }
.cfoot { font-size: 5.8pt; color: #fff; padding: 1mm 2.5mm; letter-spacing: .05em; }
.back { position: absolute; inset: 2.2mm; border-radius: 3mm; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #fff; text-align: center; }
.back .big { font-size: 17pt; font-weight: 800; letter-spacing: .08em; }
.back .mid { font-size: 10pt; font-weight: 700; margin-top: 2mm; letter-spacing: .12em; }
.back .small { font-size: 7pt; margin-top: 3mm; opacity: .9; }
.back .logo { position: absolute; bottom: 4mm; font-size: 6.5pt; letter-spacing: .2em; opacity: .85; }
.back .ring { width: 30mm; height: 30mm; border-radius: 50%; border: 1.2mm solid rgba(255,255,255,.55); display: flex; align-items: center; justify-content: center; margin-bottom: 3mm; }
/* referência */
.ref { font-size: 6.4pt; line-height: 1.28; padding: 1.8mm 2.4mm; }
.ref table { width: 100%; border-collapse: collapse; }
.ref td { padding: .55mm .6mm; border-bottom: .2mm solid #ddd; vertical-align: top; }
.ref b { color: #2e5e4e; }
/* tiles */
.tiles { position: absolute; left: 10mm; top: 8mm; display: grid; grid-template-columns: repeat(3, 58mm); grid-auto-rows: 66mm; }
.tile { width: 58mm; height: 66mm; display: flex; align-items: center; justify-content: center; }
.tile svg { width: 52mm; height: 60mm; overflow: visible; }
/* tabuleiros */
.board { position: absolute; inset: 4mm; border: .6mm solid #2e5e4e; border-radius: 4mm; padding: 5mm; }
.bh { display: flex; align-items: center; gap: 4mm; margin-bottom: 3mm; }
.bh .t { font-size: 15pt; font-weight: 800; color: #2e5e4e; }
.stripe { width: 14mm; height: 8mm; border-radius: 1.5mm; }
.slot { border: .5mm dashed #8a8a80; border-radius: 3mm; width: 63mm; height: 88mm; display: flex; align-items: center; justify-content: center; text-align: center; color: #8a8a80; font-size: 8pt; font-weight: 700; letter-spacing: .08em; }
.track { display: flex; gap: 2mm; align-items: center; margin: 1mm 0 3mm; }
.cell { width: 15mm; height: 15mm; border: .5mm solid #555; border-radius: 2mm; display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: 800; font-size: 11pt; background: #fff; }
.cell small { font-size: 5.2pt; font-weight: 600; color: #666; letter-spacing: 0; text-align: center; line-height: 1.05; }
.tt { font-size: 9pt; font-weight: 800; color: #8a5a1c; letter-spacing: .06em; }
.note { font-size: 6.8pt; color: #555; }
.chk { display: inline-block; width: 4.2mm; height: 4.2mm; border: .4mm solid #555; border-radius: .8mm; vertical-align: middle; margin: 0 .8mm; background: #fff; }
.area { border: .5mm solid #555; border-radius: 3mm; background: #fff; }
.mini { border-collapse: collapse; font-size: 7pt; }
.mini th { background: #2e5e4e; color: #fff; padding: .8mm 1.4mm; font-weight: 700; }
.mini td { border: .3mm solid #ccc; padding: .8mm 1.4mm; text-align: center; background: #fff; }
/* fichas */
.tok { display: inline-flex; align-items: center; justify-content: center; border: .25mm dashed #9a9a9a; }
"""


# ------------------------------------------------------------------ tiles
def hex_svg(inner, fill, stroke='#555', dash=True):
    pts = '26,0 52,15 52,45 26,60 0,45 0,15'
    d = 'stroke-dasharray="1.2 .8"' if dash else ''
    return (f'<svg viewBox="0 0 52 60"><polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width=".35" {d}/>'
            f'<polygon points="26,2.6 49.5,16.3 49.5,43.7 26,57.4 2.5,43.7 2.5,16.3" fill="none" stroke="rgba(255,255,255,.45)" stroke-width=".5"/>'
            f'{inner}</svg>')


def svg_icon(name, x, y, s):
    body = ICON[name].replace('<svg viewBox="0 0 24 24">', '').replace('</svg>', '')
    k = s / 24
    return f'<g transform="translate({x},{y}) scale({k})">{body}</g>'


def tile_front(k, idx, usa):
    nome, bg, fg, res, risco, _ = D.BIOMAS[k]
    parts = []
    fs = 4.6 if len(nome) <= 9 else 3.7
    parts.append(f'<text x="26" y="12.5" font-size="{fs}" font-weight="700" text-anchor="middle" fill="{fg}" font-family="DejaVu Sans">{e(nome.upper())}</text>')
    icons = []
    for r, n in res.items():
        icons += [r] * n
    s = 8.5 if len(icons) <= 3 else 7.4
    total = len(icons) * s + (len(icons) - 1) * 1.2
    x0 = 26 - total / 2
    for i, r in enumerate(icons):
        parts.append(svg_icon(r, x0 + i * (s + 1.2), 22, s))
    if k == 'Re':
        parts.append(svg_icon('resgate', 18, 19, 16))
        parts.append(f'<text x="26" y="41" font-size="3" text-anchor="middle" fill="{fg}" font-family="DejaVu Sans">sem recursos · fim da prova</text>')
    elif k == 'I':
        parts.append(f'<text x="26" y="31" font-size="3.4" text-anchor="middle" fill="{fg}" font-family="DejaVu Sans">todos começam aqui</text>')
        parts.append(f'<text x="26" y="36" font-size="3" text-anchor="middle" fill="{fg}" font-family="DejaVu Sans">(começa revelado)</text>')
    elif k == 'Pa':
        parts.append(f'<text x="26" y="31" font-size="3.4" text-anchor="middle" fill="{fg}" font-family="DejaVu Sans">sem recursos</text>')
    if risco:
        parts.append(svg_icon('risco', 21.5, 33, 9))
        parts.append(f'<text x="26" y="45.2" font-size="2.5" text-anchor="middle" fill="{fg}" font-family="DejaVu Sans">Risco na 1ª coleta (d6)</text>')
    elif res:
        nomes = {'comida': ('comida', 'comidas'), 'agua': ('água', 'águas'), 'madeira': ('madeira', 'madeiras')}
        desc = ' + '.join(f'{n} {nomes[r][n > 1]}' for r, n in res.items())
        parts.append(f'<text x="26" y="39" font-size="3" text-anchor="middle" fill="{fg}" font-family="DejaVu Sans">{e(desc)}</text>')
    tag = '·'.join(str(n) for n in usa)
    parts.append(f'<text x="26" y="49.5" font-size="2.7" font-weight="700" text-anchor="middle" fill="{fg}" font-family="DejaVu Sans" opacity=".9">{tag} jogadores</text>')
    parts.append(f'<text x="26" y="52.8" font-size="2.4" text-anchor="middle" fill="{fg}" font-family="DejaVu Sans" opacity=".75">cópia {idx}</text>')
    return hex_svg(''.join(parts), bg)


def tile_back():
    inner = ('<text x="26" y="28" font-size="13" font-weight="800" text-anchor="middle" fill="#f3ead2" font-family="DejaVu Sans">?</text>'
             '<text x="26" y="38" font-size="3.3" font-weight="700" text-anchor="middle" fill="#f3ead2" font-family="DejaVu Sans" letter-spacing=".4">LARGADOS</text>'
             '<text x="26" y="42.3" font-size="3.3" font-weight="700" text-anchor="middle" fill="#f3ead2" font-family="DejaVu Sans" letter-spacing=".4">E PELADOS</text>')
    return hex_svg(inner, '#46503a')


def tile_pages():
    ts = D.tiles()
    pages = []
    for start in range(0, len(ts), 12):
        chunk = ts[start:start + 12]
        fronts = ''.join(f'<div class="tile">{tile_front(*t)}</div>' for t in chunk)
        pages.append(f'<section class="sheet"><div class="label">TILES · FRENTE ({start + 1}–{start + len(chunk)} de {len(ts)})</div><div class="tiles">{fronts}</div></section>')
        backs = []
        for row in range(0, 12, 3):
            cells = chunk[row:row + 3]
            if not cells:
                break
            row_cells = [f'<div class="tile">{tile_back()}</div>' for _ in cells] + ['<div class="tile"></div>'] * (3 - len(cells))
            backs += row_cells[::-1]
        pages.append(f'<section class="sheet"><div class="label">TILES · VERSO (espelhado para frente e verso)</div><div class="tiles">{"".join(backs)}</div></section>')
    return pages


# ------------------------------------------------------------------ cartas
def card(inner):
    return f'<div class="card">{inner}</div>'


def event_front(n, nome, fase, quando, texto, sabor):
    cor, rod = D.FASES[fase]
    return card(f'<div class="cin" style="background:#fffdf7;border:.4mm solid {cor}">'
                f'<div class="chead" style="background:{cor}"><span>EVENTO · {fase.upper()}</span><span>{n:02d}</span></div>'
                f'<div class="ctitle">{e(nome)}</div>'
                f'<div class="ctime" style="background:{cor}22;color:{cor}">{e(quando.upper())}</div>'
                f'<div class="ctext">{e(texto)}</div>'
                f'<div class="cflav">{e(sabor)}</div>'
                f'<div class="cfoot" style="background:{cor}">{e(rod)} · Sofá: sorteio livre</div></div>')


def event_back(fase):
    cor, rod = D.FASES[fase]
    return card(f'<div class="back" style="background:{cor}"><div class="ring">{icon("fogo", "14mm") if fase == "Dura" else icon("agua", "14mm") if fase == "Leve" else icon("risco", "14mm")}</div>'
                f'<div class="big">EVENTO</div><div class="mid">{fase.upper()}</div><div class="small">{e(rod)}</div>'
                f'<div class="logo">LARGADOS E PELADOS</div></div>')


def item_front(nome, texto, sabor):
    cor = '#2c6f7a'
    return card(f'<div class="cin" style="background:#f6fbfb;border:.4mm solid {cor}">'
                f'<div class="chead" style="background:{cor}"><span>ITEM INICIAL</span><span>USO ÚNICO</span></div>'
                f'<div class="ctitle">{e(nome)}</div>'
                f'<div class="ctext" style="margin-top:1mm">{e(texto)}</div>'
                f'<div class="cflav">{e(sabor)}</div>'
                f'<div class="cfoot" style="background:{cor}">Descarte ao usar · guardado no fim = +1 PS</div></div>')


def item_back():
    return card('<div class="back" style="background:#2c6f7a"><div class="ring">' + icon('abrigo', '13mm') + '</div>'
                '<div class="big">ITEM</div><div class="small">1 por pessoa na preparação</div><div class="logo">LARGADOS E PELADOS</div></div>')


def arq_front(nome, texto, sabor, so_av):
    cor = '#8a5a1c'
    extra = '<div class="ctime" style="background:#c0392b22;color:#c0392b">SÓ MODO AVANÇADO</div>' if so_av else ''
    return card(f'<div class="cin" style="background:#fdf8f0;border:.4mm solid {cor}">'
                f'<div class="chead" style="background:{cor}"><span>ARQUÉTIPO</span><span>HABILIDADE</span></div>'
                f'<div class="ctitle">{e(nome)}</div>{extra}'
                f'<div class="ctext">{e(texto)}</div>'
                f'<div class="cflav">{e(sabor)}</div>'
                f'<div class="cfoot" style="background:{cor}">Usos semanais voltam nas rodadas 4 e 7</div></div>')


def arq_back():
    return card('<div class="back" style="background:#8a5a1c"><div class="ring" style="font-size:20pt;font-weight:800">★</div>'
                '<div class="big">ARQUÉTIPO</div><div class="small">escolha 1 diferente de cada pessoa</div><div class="logo">LARGADOS E PELADOS</div></div>')


def ref_front():
    rows = ''.join(f'<tr><td><b>{e(a)}</b></td><td style="white-space:nowrap">{e(c)}</td><td>{e(t)}</td></tr>' for a, c, t in D.ACOES)
    return card('<div class="cin" style="background:#fff;border:.4mm solid #2e5e4e">'
                '<div class="chead" style="background:#2e5e4e"><span>REFERÊNCIA</span><span>AÇÕES E CUSTOS</span></div>'
                f'<div class="ref"><table>{rows}</table>'
                '<p style="margin:1.2mm 0 0"><b>4 PE por vez.</b> Avançado: com 1+ Desgaste, 3 PE. Itens e habilidades não gastam PE. Limite: 4 comidas.</p></div></div>')


def ref_back():
    return card('<div class="cin" style="background:#fff;border:.4mm solid #2e5e4e">'
                '<div class="chead" style="background:#2e5e4e"><span>REFERÊNCIA</span><span>RODADA E PROVA</span></div>'
                '<div class="ref"><b>1. Evento</b> (não há na rodada 1) · <b>2. Vezes</b> a partir do 1º jogador · '
                '<b>3. Fim</b>: tire os Coletado · <b>4. Prova</b> após as rodadas 3, 6, 9; apague os fogos; 1º jogador à esquerda.'
                '<table style="margin-top:1.2mm"><tr><td><b>Prova</b></td><td><b>Comida</b></td><td><b>Água</b></td></tr>'
                '<tr><td>Avançado comp.</td><td>2 · 2 · 2</td><td>1 · 1 · 1</td></tr>'
                '<tr><td>Avançado coop 2p</td><td>1 · 2 · 2</td><td>1 · 1 · 1</td></tr>'
                '<tr><td>Avançado coop 3p</td><td>1 · 1 · 2</td><td>1 · 1 · 1</td></tr>'
                '<tr><td>Avançado coop 4p</td><td>1 · 1 · 1</td><td>1 · 1 · 1</td></tr>'
                '<tr><td>Sofá comp. / coop 2p</td><td>2 · 3</td><td>1 · 1</td></tr>'
                '<tr><td>Sofá coop 3–4p</td><td>2 · 2</td><td>1 · 1</td></tr></table>'
                '<p style="margin:1mm 0 0">Falta numa categoria = 1 Desgaste (sem pagamento parcial). Água sem fogo (Avançado): d6 ímpar = Desgaste. '
                'Fim: abrigo 3 (Sofá 2) e peão em Resgate.</p></div></div>')


def card_pages(fronts, backs, titulo):
    """fronts/backs: listas paralelas; a página de verso espelha as colunas."""
    pages = []
    for s in range(0, len(fronts), 9):
        f = fronts[s:s + 9]
        b = backs[s:s + 9]
        pages.append(f'<section class="sheet"><div class="label">{titulo} · FRENTE</div><div class="cards">{"".join(f)}</div></section>')
        mirrored = []
        for row in range(0, 9, 3):
            cells = b[row:row + 3]
            if not cells:
                break
            cells = cells + ['<div class="card" style="border:none"></div>'] * (3 - len(cells))
            mirrored += cells[::-1]
        pages.append(f'<section class="sheet"><div class="label">{titulo} · VERSO (espelhado para frente e verso)</div><div class="cards">{"".join(mirrored)}</div></section>')
    return pages


# ------------------------------------------------------------- tabuleiros
def track(values, labels=None, width='15mm'):
    labels = labels or [''] * len(values)
    return '<div class="track">' + ''.join(
        f'<div class="cell" style="width:{width}">{v}{f"<small>{l}</small>" if l else ""}</div>' for v, l in zip(values, labels)) + '</div>'


def individual_board(cor_nome, cor):
    semanas = ''.join(
        f'<div style="display:flex;align-items:center;gap:1.5mm;margin-bottom:1.6mm;font-size:8pt">'
        f'<b style="width:17mm">Semana {w}</b>Prova concluída<span class="chk"></span>'
        f'&nbsp;Habilidade<span class="chk"></span>&nbsp;Descanso<span class="chk"></span></div>' for w in (1, 2, 3))
    return f'''<section class="sheet land"><div class="board" style="border-color:{cor}">
<div class="bh"><div class="stripe" style="background:{cor}"></div><div class="t">TABULEIRO INDIVIDUAL</div>
<div style="font-size:9pt;color:#666">Cor: <b style="color:{cor}">{cor_nome}</b> · Participante: ________________________</div></div>
<div style="display:flex;gap:6mm">
 <div>
  <div style="display:flex;gap:4mm"><div class="slot">ARQUÉTIPO<br>(carta)</div><div class="slot">ITEM<br>(carta)</div></div>
  <div style="margin-top:4mm">{semanas}</div>
  <div class="note" style="width:130mm">Marque os usos semanais e apague-os nas rodadas 4 e 7. No Sofá não há semana 3.</div>
 </div>
 <div style="flex:1">
  <div class="tt">ENERGIA (PE)</div>{track([0, 1, 2, 3, 4])}
  <div class="tt">DESGASTE</div>{track([0, 1, 2, 3], ['', 'Avançado:<br>3 PE', '', 'ELIMINADO'])}
  <div class="tt">ABRIGO (nível)</div>{track([0, 1, 2, 3], ['', '', 'Sofá: fim', 'Avançado: fim'])}
  <div style="display:flex;gap:5mm;align-items:flex-start">
   <div><div class="tt">COMIDA (máx. 4)</div><div class="track">{''.join(f'<div class="cell" style="width:15mm;height:15mm">{icon("comida", "8mm")}</div>' for _ in range(4))}</div></div>
   <div><div class="tt">FOGO</div><div class="cell" style="width:30mm;height:15mm;font-size:7pt">{icon("fogo", "8mm")} aceso? (Avançado)</div></div>
  </div>
  <div style="display:flex;gap:5mm">
   <div><div class="tt">ÁGUA</div><div class="area" style="width:62mm;height:34mm;display:flex;align-items:center;justify-content:center;opacity:.9">{icon("agua", "9mm")}</div></div>
   <div><div class="tt">MADEIRA</div><div class="area" style="width:62mm;height:34mm;display:flex;align-items:center;justify-content:center">{icon("madeira", "9mm")}</div></div>
  </div>
  <div class="note" style="margin-top:2mm">Prova: pague a comida e a água que estão aqui. Falta numa categoria = 1 Desgaste. Sobra de comida continua (limite 4).</div>
 </div>
</div></div></section>'''


def round_box(r, fases_comp, fases_coop, prova):
    def chip(f):
        if not f:
            return '<span style="color:#999">sem Evento</span>'
        cor = D.FASES[f][0]
        return f'<span style="background:{cor};color:#fff;border-radius:1mm;padding:.3mm 1.2mm;font-weight:700">{f}</span>'
    extra = f'<div style="margin-top:1.2mm;font-size:6.5pt;font-weight:800;color:#c0392b">▶ PROVA {prova}</div>' if prova else ''
    return (f'<div style="border:.5mm solid #555;border-radius:2mm;background:#fff;width:25.5mm;height:40mm;padding:1.4mm;font-size:6.4pt;line-height:1.5">'
            f'<div style="font-size:15pt;font-weight:800;color:#2e5e4e;line-height:1">{r}</div>'
            f'<div>Comp.: {chip(fases_comp)}</div><div>Coop: {chip(fases_coop)}</div>{extra}</div>')


def collective_board():
    comp = {1: None, 2: 'Leve', 3: 'Leve', 4: 'Mista', 5: 'Mista', 6: 'Mista', 7: 'Dura', 8: 'Dura', 9: 'Dura'}
    coop = {**comp, 7: 'Mista'}
    semanas = [('Semana 1 · Chegada', '#3f9e4d', (1, 2, 3)), ('Semana 2 · Adaptação', '#d19a2a', (4, 5, 6)),
               ('Semana 3 · Reta final', '#c0392b', (7, 8, 9))]
    blocos = ''
    for nome, cor, rs in semanas:
        caixas = ''.join(round_box(r, comp[r], coop[r], (r // 3) if r % 3 == 0 else None) for r in rs)
        blocos += (f'<div><div style="background:{cor};color:#fff;font-weight:800;font-size:8pt;padding:1mm 2mm;border-radius:1.5mm 1.5mm 0 0">{nome}</div>'
                   f'<div style="display:flex;gap:1.2mm;padding:1.2mm;background:{cor}1a;border-radius:0 0 1.5mm 1.5mm">{caixas}</div></div>')
    sofa = ''.join(f'<div class="cell" style="width:12mm;height:11mm;font-size:10pt">{r}{"<small>PROVA</small>" if r % 3 == 0 else ""}</div>' for r in range(1, 7))
    slots = ''.join(f'<div class="slot" style="width:55mm;height:77mm">{t}</div>' for t in ('PILHA DE<br>EVENTOS', 'EVENTO<br>DA RODADA', 'DESCARTE'))
    tabela = ('<table class="mini"><tr><th>Prova · Avançado</th><th>Comida</th><th>Água</th></tr>'
              '<tr><td>Competitivo</td><td>2 · 2 · 2</td><td>1 · 1 · 1</td></tr>'
              '<tr><td>Coop 2 pessoas</td><td>1 · 2 · 2</td><td>1 · 1 · 1</td></tr>'
              '<tr><td>Coop 3 pessoas</td><td>1 · 1 · 2</td><td>1 · 1 · 1</td></tr>'
              '<tr><td>Coop 4 pessoas</td><td>1 · 1 · 1</td><td>1 · 1 · 1</td></tr>'
              '<tr><th>Prova · Sofá</th><th>Comida</th><th>Água</th></tr>'
              '<tr><td>Comp. / Coop 2p</td><td>2 · 3</td><td>1 · 1</td></tr>'
              '<tr><td>Coop 3–4 pessoas</td><td>2 · 2</td><td>1 · 1</td></tr></table>')
    return f'''<section class="sheet land"><div class="board">
<div class="bh"><div class="t">TABULEIRO COLETIVO · MODO AVANÇADO</div><div style="font-size:8pt;color:#666">Mova o marcador de rodada. O 1º jogador passa à esquerda a cada rodada.</div></div>
<div style="display:flex;gap:1.6mm">{blocos}</div>
<div style="display:flex;gap:5mm;margin-top:3mm;align-items:flex-start">
 <div style="display:flex;gap:3mm">{slots}</div>
 <div>{tabela}
  <div class="tt" style="margin-top:2.5mm">MODO SOFÁ · 6 RODADAS</div><div class="track">{sofa}</div>
  <div class="note" style="width:92mm">Sofá: 5 Eventos sorteados (rodadas 2–6), sem fases. Fim: abrigo 2 e Resgate.</div>
 </div>
</div></div></section>'''


# ------------------------------------------------------------------ fichas
def token(inner, size=15, shape='circle', border='#9a9a9a', bg='#fff'):
    rad = '50%' if shape == 'circle' else '2mm'
    return (f'<div class="tok" style="width:{size}mm;height:{size}mm;border-radius:{rad};background:{bg};border-color:{border}">{inner}</div>')


def token_pages():
    res = []
    for nome, qtd in (('comida', 60), ('agua', 36), ('madeira', 24)):
        res += [token(icon(nome, '10mm'), 15)] * qtd
    p1 = (f'<section class="sheet"><div class="label">RECURSOS · 60 comidas, 36 águas, 24 madeiras (recorte os círculos)</div>'
          f'<div style="position:absolute;left:3mm;top:6mm;display:flex;flex-wrap:wrap;gap:.8mm;width:190mm">{"".join(res)}</div></section>')
    col = [token('<div style="text-align:center;font-size:5.2pt;font-weight:800;color:#2e5e4e">' + icon('check', '8mm') + '<br>COLETADO</div>', 17, 'sq')] * 16
    risco = [token(icon('risco', '12mm'), 17, 'sq', bg='#fff8dc')] * 7
    pessoais = []
    for nome, cor in D.CORES_JOGADORES:
        pessoais.append(token(f'<div style="text-align:center;font-size:5pt;font-weight:800;color:#fff">{icon("abrigo", "9mm")}<br>ABRIGO</div>', 17, 'sq', bg=cor))
        pessoais.append(token(f'<div style="text-align:center;font-size:5pt;font-weight:800;color:#fff">{icon("fogo", "9mm")}<br>FOGO ACESO</div>', 17, 'circle', bg=cor))
        for t in ('PE', 'DESG.', 'NÍVEL'):
            pessoais.append(token(f'<div style="font-size:6.5pt;font-weight:800;color:#fff">{t}</div>', 11, 'circle', bg=cor))
    rodada = token('<div style="text-align:center;font-size:6pt;font-weight:800">RODADA</div>', 17, 'circle', bg='#f3ead2')
    primeiro = token('<div style="text-align:center;font-size:5.4pt;font-weight:800">1º<br>JOGADOR</div>', 17, 'sq', bg='#f3ead2')
    standees = ''.join(
        f'<div style="width:22mm;height:44mm;border:.25mm dashed #9a9a9a;display:flex;flex-direction:column">'
        f'<div style="flex:1;background:{cor};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:7pt;transform:rotate(180deg)">{nome.upper()}</div>'
        f'<div style="flex:1;background:{cor};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:7pt;border-top:.3mm dotted #fff">{nome.upper()}</div></div>'
        for nome, cor in D.CORES_JOGADORES)
    p2 = (f'<section class="sheet"><div class="doc" style="padding:2mm 3mm">'
          f'<h3>Marcadores Coletado (16) e Risco (7)</h3><div style="display:flex;flex-wrap:wrap;gap:1mm">{"".join(col + risco)}</div>'
          f'<h3>Marcadores pessoais (por cor: abrigo, fogo, energia, Desgaste, nível do abrigo)</h3>'
          f'<div style="display:flex;flex-wrap:wrap;gap:1mm;align-items:center">{"".join(pessoais)}</div>'
          f'<h3>Rodada e primeiro jogador</h3><div style="display:flex;gap:2mm">{rodada}{primeiro}</div>'
          f'<h3>Peões de papel (dobre ao meio e cole a base, ou use peões de outro jogo)</h3><div style="display:flex;gap:3mm">{standees}</div>'
          f'</div></section>')
    return [p1, p2]


# ------------------------------------------------------------------ guia
def guide_pages(npag):
    contagem = ''.join(f'<tr><td>{e(D.BIOMAS[k][0])}</td><td>{" · ".join(str(c) for c in D.BIOMAS[k][5])}</td>'
                       f'<td>{max(D.BIOMAS[k][5])}</td></tr>' for k in D.ORDEM_BIOMAS)
    capa = f'''<section class="sheet"><div class="doc">
<h1>Largados e Pelados<br>Manual de prototipagem</h1>
<p class="sub">Versão 0.5 · kit completo para imprimir, recortar e jogar (Modo Sofá e Modo Avançado)</p>
<div class="box">Este kit acompanha o <b>Manual de regras 0.5</b>. Tudo o que está aqui foi desenhado para <b>impressão caseira em A4</b>: cartas no tamanho de baralho (63 × 88 mm), tiles hexagonais de 60 mm e marcadores para recortar.</div>
<h2>O que tem no kit</h2>
<table><thead><tr><th>Componente</th><th>Quantidade</th><th>Páginas</th><th>Como imprimir</th></tr></thead><tbody>
<tr><td>Tiles hexagonais (frente e verso)</td><td>31</td><td>{npag["tiles"]}</td><td>Frente e verso, virar pela borda longa</td></tr>
<tr><td>Cartas de Evento (verso com a fase)</td><td>18</td><td>{npag["eventos"]}</td><td>Frente e verso, virar pela borda longa</td></tr>
<tr><td>Itens, Arquétipos e Referência</td><td>5 + 7 + 4</td><td>{npag["outras"]}</td><td>Frente e verso, virar pela borda longa</td></tr>
<tr><td>Tabuleiros individuais (A4 deitado)</td><td>4</td><td>{npag["individuais"]}</td><td>Só frente</td></tr>
<tr><td>Tabuleiro coletivo (A4 deitado)</td><td>1</td><td>{npag["coletivo"]}</td><td>Só frente</td></tr>
<tr><td>Recursos, marcadores e peões</td><td>120 recursos + marcadores</td><td>{npag["fichas"]}</td><td>Só frente</td></tr>
<tr><td>Ficha de playtest</td><td>1 (copie à vontade)</td><td>{npag["playtest"]}</td><td>Só frente</td></tr>
</tbody></table>
<h2>O que providenciar</h2>
<ul><li><b>1 dado de seis faces (d6).</b></li>
<li><b>4 peões</b> (de outro jogo ou os peões de papel do kit).</li>
<li><b>Papel:</b> sulfite 90 g para tudo, ou 180 g para cartas e tiles. Papelão cinza (1–2 mm) ou papel cartão para colar os tiles e os tabuleiros deixa tudo mais firme.</li>
<li><b>Tesoura ou estilete, régua e cola em bastão.</b></li>
<li><i>Opcional:</i> 34 sleeves de 63,5 × 88 mm com uma carta comum dentro para dar corpo; saquinhos zip para separar recursos; grãos ou botões no lugar das fichas de recurso (feijão = comida, milho = água, palito = madeira).</li></ul>
<h2>Como imprimir</h2>
<ol><li>Imprima em <b>A4, escala 100%</b> ("tamanho real"; desligue "ajustar à página").</li>
<li>As páginas de <b>tiles e cartas</b> vêm em pares frente/verso, com o verso já espelhado. Imprima esse intervalo em <b>frente e verso, virando pela borda longa</b>. Sem impressora duplex, imprima só as frentes e as páginas de verso separadamente e cole uma na outra antes de recortar.</li>
<li>Os <b>tabuleiros</b> saem em A4 deitado; imprima só a frente.</li>
<li>Recorte nas <b>linhas tracejadas</b>.</li></ol>
</div></section>'''
    montagem = f'''<section class="sheet"><div class="doc">
<h2>Montagem passo a passo</h2>
<ol><li><b>Tiles:</b> cole a folha de frente e verso sobre papelão, espere secar e recorte os hexágonos. O canto inferior de cada tile mostra <b>com quantas pessoas ele entra</b> (ex.: "3·4 jogadores") e o número da cópia.</li>
<li><b>Cartas:</b> recorte e, se quiser, coloque em sleeves. O <b>verso dos Eventos tem a cor da fase</b> (verde = Leve, amarelo = Mista, vermelho = Dura): é assim que se monta a pilha em fases na preparação.</li>
<li><b>Tabuleiros:</b> cole sobre papel cartão. Os tabuleiros individuais têm espaço para as cartas de Arquétipo e Item, as trilhas de energia, Desgaste e abrigo, os espaços de comida (máximo 4), água e madeira, e caixas para marcar Provas e usos semanais.</li>
<li><b>Marcadores:</b> recorte os recursos (círculos), os Coletado, os Risco e os marcadores pessoais das 4 cores.</li>
<li><b>Organize:</b> um saquinho para cada recurso e um para os tiles de cada tipo facilitam a montagem do mapa.</li></ol>
<h2>Conferência dos tiles</h2>
<table><thead><tr><th>Tile</th><th>Usados com 2 · 3 · 4 pessoas</th><th>Cópias no kit</th></tr></thead><tbody>{contagem}
<tr><td><b>Total</b></td><td><b>20 · 25 · 30</b></td><td><b>31</b></td></tr></tbody></table>
<p>Com 4 pessoas o Pasto fica na caixa e entra a 6ª Clareira; com 2 ou 3, o Pasto entra e as Clareiras extras ficam fora.</p>
<h2>Conferência das cartas</h2>
<table><thead><tr><th>Tipo</th><th>Quantidade</th><th>Detalhe</th></tr></thead><tbody>
<tr><td>Eventos</td><td>18</td><td>8 Leves, 5 Mistas, 5 Duras</td></tr>
<tr><td>Itens</td><td>5</td><td>Faca, Panela, Cantil, Rede de pesca, Toldo</td></tr>
<tr><td>Arquétipos</td><td>7</td><td>Guardião do Fogo só no Modo Avançado</td></tr>
<tr><td>Referência</td><td>4</td><td>Frente: ações e custos · verso: rodada e Prova</td></tr></tbody></table>
<h2>Dicas para o playtest</h2>
<ul><li>Comece pelo <b>Modo Sofá</b> com quem nunca jogou; cronometre a partida.</li>
<li>Use a <b>ficha de playtest</b> no fim do kit para anotar sintomas (o que as pessoas sentiram, onde travaram). É o insumo para o próximo raio-X do método do curso.</li>
<li>Anote em que rodada cada pessoa foi eliminada e se a tensão cresceu até a Prova final.</li></ul>
</div></section>'''
    return [capa, montagem]


def playtest_page():
    linhas = lambda n: ''.join('<div style="border-bottom:.3mm solid #bbb;height:7mm"></div>' for _ in range(n))
    return f'''<section class="sheet"><div class="doc">
<h2>Ficha de playtest</h2>
<table><tbody>
<tr><td style="width:40%">Data · local</td><td></td></tr>
<tr><td>Modo (Sofá / Avançado) · competitivo ou cooperativo</td><td></td></tr>
<tr><td>Nº de pessoas · quem já conhecia o jogo</td><td></td></tr>
<tr><td>Duração (preparação / partida)</td><td></td></tr>
<tr><td>Quem concluiu · PS de cada pessoa</td><td></td></tr>
<tr><td>Eliminações (quem, em que rodada, por quê)</td><td></td></tr>
<tr><td>Eventos que apareceram (na ordem)</td><td></td></tr>
</tbody></table>
<h3>De 0 a 5, quanto a mesa sentiu...</h3>
<table><tbody>
<tr><td>Tensão "no limite" (5 = por um fio até o fim)</td><td>0 1 2 3 4 5</td></tr>
<tr><td>Vontade de jogar de novo</td><td>0 1 2 3 4 5</td></tr>
<tr><td>Clareza das regras</td><td>0 1 2 3 4 5</td></tr>
<tr><td>Tempo parado esperando a vez (5 = muito)</td><td>0 1 2 3 4 5</td></tr></tbody></table>
<h3>Momentos marcantes (o que as pessoas comentaram depois)</h3>{linhas(4)}
<h3>Onde a mesa travou ou precisou consultar o manual</h3>{linhas(4)}
<h3>Sintomas observados (lentes do curso: escolhas, loop de diversão, fluidez, ritmo)</h3>{linhas(5)}
<h3>Ideias de mudança para o próximo teste</h3>{linhas(3)}
</div></section>'''


def main():
    tiles = tile_pages()
    ev_f = [event_front(*ev) for ev in D.EVENTOS]
    ev_b = [event_back(ev[2]) for ev in D.EVENTOS]
    eventos = card_pages(ev_f, ev_b, 'CARTAS DE EVENTO')
    of = [item_front(*i) for i in D.ITENS] + [arq_front(*a) for a in D.ARQUETIPOS] + [ref_front() for _ in range(4)]
    ob = [item_back() for _ in D.ITENS] + [arq_back() for _ in D.ARQUETIPOS] + [ref_back() for _ in range(4)]
    outras = card_pages(of, ob, 'ITENS · ARQUÉTIPOS · REFERÊNCIA')
    individuais = [individual_board(n, c) for n, c in D.CORES_JOGADORES]
    coletivo = [collective_board()]
    fichas = token_pages()
    play = [playtest_page()]
    # numeração das páginas (o guia ocupa 2)
    start = 3
    npag = {}
    for nome, lst in (('tiles', tiles), ('eventos', eventos), ('outras', outras), ('individuais', individuais),
                      ('coletivo', coletivo), ('fichas', fichas), ('playtest', play)):
        npag[nome] = f'{start}–{start + len(lst) - 1}' if len(lst) > 1 else f'{start}'
        start += len(lst)
    pages = guide_pages(npag) + tiles + eventos + outras + individuais + coletivo + fichas + play
    doc = (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Manual de prototipagem 0.5</title>'
           f'<style>{CSS}</style></head><body>{"".join(pages)}</body></html>')
    open(OUT_HTML, 'w', encoding='utf-8').write(doc)
    chrome = sorted(glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome'))[-1]
    subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={OUT_PDF}', 'file://' + OUT_HTML], check=True, capture_output=True)
    print(OUT_PDF, npag)


if __name__ == '__main__':
    main()
