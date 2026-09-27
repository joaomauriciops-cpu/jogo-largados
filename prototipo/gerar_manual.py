"""Gera o PDF do manual de regras a partir do Markdown.

    python3 gerar_manual.py
"""
import glob
import os
import subprocess

from md2html import convert

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SRC = os.path.join(RAIZ, 'manual', 'MANUAL_DE_REGRAS_0.5.md')
OUT_HTML = os.path.join(RAIZ, 'manual', 'manual_0.5.html')
OUT_PDF = os.path.join(RAIZ, 'manual', 'Manual_de_Regras_Largados_e_Pelados_0.5.pdf')

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm;
  @top-left { content: "LARGADOS E PELADOS  /  MANUAL DE REGRAS 0.5"; font: 600 7.5pt 'DejaVu Sans'; color: #6b6b5e; letter-spacing: .08em; }
  @top-right { content: "PROTÓTIPO"; font: 600 7.5pt 'DejaVu Sans'; color: #6b6b5e; letter-spacing: .08em; }
  @bottom-right { content: counter(page); font: 8pt 'DejaVu Sans'; color: #6b6b5e; } }
@page :first { @top-left { content: none; } @top-right { content: none; } }
body { font-family: 'DejaVu Sans', 'Liberation Sans', sans-serif; font-size: 9.6pt; line-height: 1.42; color: #22241f; }
h1 { font-size: 30pt; color: #2e5e4e; margin: 0 0 4mm; line-height: 1.1; }
h1 + p { font-size: 10.5pt; color: #8a5a1c; margin-bottom: 8mm; }
h2 { font-size: 14pt; color: #2e5e4e; border-bottom: 1.5pt solid #c8913b; padding-bottom: 1.5mm; margin: 7mm 0 3mm; break-after: avoid; }
h3 { font-size: 11pt; color: #8a5a1c; margin: 5mm 0 2mm; break-after: avoid; }
p { margin: 0 0 2.4mm; }
ul, ol { margin: 0 0 2.6mm; padding-left: 6mm; }
li { margin-bottom: 1mm; }
li > ul, li > ol { margin-top: 1mm; }
table { width: 100%; border-collapse: collapse; margin: 1.5mm 0 4mm; font-size: 8.6pt; break-inside: auto; }
tr { break-inside: avoid; }
th { background: #2e5e4e; color: #fff; text-align: left; padding: 1.6mm 2mm; font-weight: 600; }
td { border-bottom: .5pt solid #cfd6cf; padding: 1.4mm 2mm; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f2f5f3; }
blockquote { margin: 2mm 0 4mm; padding: 2.5mm 4mm; background: #fbf5ea; border-left: 3pt solid #c8913b; }
strong { color: #1d3b31; }
em { color: #555; }
"""


def main():
    md = open(SRC, encoding='utf-8').read()
    body = convert(md)
    html = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Manual de regras 0.5</title><style>{CSS}</style></head><body>{body}</body></html>'
    open(OUT_HTML, 'w', encoding='utf-8').write(html)
    chrome = sorted(glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome'))[-1]
    subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={OUT_PDF}', 'file://' + OUT_HTML],
                   check=True, capture_output=True)
    print(OUT_PDF)


if __name__ == '__main__':
    main()
