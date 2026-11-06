"""Generate a two-page A4-landscape approach note from APPROACH.md, without fonts/files tied to Windows.

    python docs/make_approach.py approach_note.pdf

The Markdown is authoritative. The PDF contains the same four required parts and
intentionally uses a page break between parts 2 and 3 for a predictable two-page layout.
"""
import html
from pathlib import Path
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parent.parent
NAVY = colors.HexColor('#1F3A5F')
LIGHT = colors.HexColor('#EEF2F7')
GREY = colors.HexColor('#8A94A6')
TITLE = ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=14.5, leading=17, spaceAfter=7)
SUB = ParagraphStyle('sub', fontName='Helvetica-Bold', fontSize=10.2, leading=12, textColor=NAVY,
                     spaceBefore=8, spaceAfter=4)
BODY = ParagraphStyle('body', fontName='Helvetica', fontSize=8.5, leading=11, spaceAfter=5)
BULLET = ParagraphStyle('bullet', parent=BODY, leftIndent=11, firstLineIndent=-8, spaceAfter=3)
TABLE = ParagraphStyle('table', parent=BODY, fontSize=8.1, leading=10.1, spaceAfter=0)
TH = ParagraphStyle('th', parent=TABLE, fontName='Helvetica-Bold', textColor=colors.white)
META = ParagraphStyle('meta', parent=BODY, fontSize=8.7, leading=11.4, spaceAfter=3)


def inline_md(s):
    s = html.escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'`(.+?)`', r'<font name="Courier">\1</font>', s)
    s = re.sub(r'\*(.+?)\*', r'<i>\1</i>', s)
    return s.replace('  ', ' ')


def parse_table(lines):
    data = []
    for line in lines:
        cells = [x.strip() for x in line.strip().strip('|').split('|')]
        if all(re.fullmatch(r':?-{3,}:?', x) for x in cells):
            continue
        data.append(cells)
    n = len(data[0])
    if any(len(row) != n for row in data):
        raise ValueError('Markdown table with inconsistent column count')
    width = [54*mm, 225*mm] if n == 2 else None
    out = [[Paragraph(inline_md(cell), TH if i == 0 else TABLE) for cell in row]
           for i, row in enumerate(data)]
    table = Table(out, colWidths=width, hAlign='LEFT', repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
        ('GRID',(0,0),(-1,-1),.4,GREY),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))
    return table


def render(md_text):
    lines = md_text.splitlines()
    result = []
    i = 0
    part_no = 0
    while i < len(lines):
        raw = lines[i]
        if not raw.strip():
            i += 1; continue
        if raw.startswith('# '):
            result.append(Paragraph(inline_md(raw[2:]), TITLE)); i += 1; continue
        if raw.startswith('## '):
            part_no += 1
            if part_no == 3:
                result.append(PageBreak())
            result.append(Paragraph(inline_md(raw[3:]), SUB)); i += 1; continue
        if raw.startswith('|'):
            start = i
            while i < len(lines) and lines[i].startswith('|'):
                i += 1
            result.append(parse_table(lines[start:i]))
            result.append(Spacer(1, 4))
            continue
        if raw.startswith('- '):
            result.append(Paragraph('&#8226; ' + inline_md(raw[2:]), BULLET)); i += 1; continue
        para = [raw.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(('# ', '## ', '|', '- ')):
            para.append(lines[i].strip()); i += 1
        result.append(Paragraph(inline_md(' '.join(para)), META if part_no == 0 else BODY))
    return result


def main(path='approach_note.pdf'):
    md_text = (ROOT/'APPROACH.md').read_text(encoding='utf-8')
    doc = SimpleDocTemplate(path, pagesize=landscape(A4), leftMargin=9*mm,
                            rightMargin=9*mm, topMargin=7*mm, bottomMargin=7*mm,
                            title='LIFELINE approach note - Iteration 1',
                            author='Group 18')
    doc.build(render(md_text))
    print(f'created {path} from APPROACH.md')

if __name__ == '__main__':
    main(*sys.argv[1:2])
