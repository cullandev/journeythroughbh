"""Builds the Word templates in this folder.

Needs python-docx (pip install python-docx). Run from anywhere:

    python brand/templates/make_templates.py

Edit the PRACTICE details below if the address, phone, or email change, then
run it again; every template is rewritten.
"""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = Path(__file__).resolve().parent
LOGO = HERE / "assets" / "header-logo.png"

PRACTICE = {
    "name": "Journey Through Behavioral Health",
    "clinician": "Jessica Cullan, LCSW",
    "title": "Licensed Clinical Social Worker",
    "street": "214 C Providence Road",
    "city": "Brooklyn, CT 06234",
    "phone": "(860) 968-3114",
    "email": "jessica@journeythroughbh.org",
    "web": "journeythroughbh.org",
}

INK = RGBColor(0x2C, 0x46, 0x36)
CLAY = RGBColor(0x98, 0x42, 0x1F)
STONE = RGBColor(0x57, 0x5B, 0x55)
TEXT = RGBColor(0x22, 0x22, 0x22)
HEAD_FONT = "Georgia"
BODY_FONT = "Calibri"
LINE_HEX = "D9D1C3"
TINT_HEX = "F3E7D6"
INK_HEX = "2C4636"


# ---------- low-level helpers ----------

def set_font(run, name=BODY_FONT, size=None, color=None, bold=None, italic=None):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), name)
    if size is not None:
        run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = color
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    return run


def spacing(par, before=0, after=0, line=None):
    fmt = par.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    if line is not None:
        fmt.line_spacing = line
    return par


def border(par, side="bottom", color=INK_HEX, size=6, space=6):
    ppr = par._p.get_or_add_pPr()
    pbdr = ppr.find(qn("w:pBdr"))
    if pbdr is None:
        pbdr = OxmlElement("w:pBdr")
        ppr.append(pbdr)
    el = OxmlElement(f"w:{side}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(size))
    el.set(qn("w:space"), str(space))
    el.set(qn("w:color"), color)
    pbdr.append(el)


def field(par, instr, **font):
    """Insert a Word field such as PAGE or NUMPAGES."""
    for kind, text in (("begin", None), (None, instr), ("separate", None), (None, "1"), ("end", None)):
        run = par.add_run()
        set_font(run, **font)
        if kind:
            ch = OxmlElement("w:fldChar")
            ch.set(qn("w:fldCharType"), kind)
            run._r.append(ch)
        elif text == instr:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = f" {instr} "
            run._r.append(it)
        else:
            run.text = text


def cell_fmt(cell, fill=None, borders=None, margins=(80, 110, 80, 110)):
    tcpr = cell._tc.get_or_add_tcPr()
    if fill:
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), fill)
        tcpr.append(shd)
    if borders is not None:
        tcb = OxmlElement("w:tcBorders")
        for side in ("top", "left", "bottom", "right"):
            el = OxmlElement(f"w:{side}")
            spec = borders.get(side)
            if spec:
                el.set(qn("w:val"), "single")
                el.set(qn("w:sz"), str(spec[1]))
                el.set(qn("w:space"), "0")
                el.set(qn("w:color"), spec[0])
            else:
                el.set(qn("w:val"), "nil")
            tcb.append(el)
        tcpr.append(tcb)
    mar = OxmlElement("w:tcMar")
    for side, val in zip(("top", "start", "bottom", "end"), margins):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tcpr.append(mar)


def fixed_table(doc, widths_in):
    table = doc.add_table(rows=0, cols=len(widths_in))
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    tblpr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblpr.append(layout)
    tblw = tblpr.find(qn("w:tblW"))
    if tblw is None:
        tblw = OxmlElement("w:tblW")
        tblpr.append(tblw)
    tblw.set(qn("w:type"), "dxa")
    tblw.set(qn("w:w"), str(int(sum(widths_in) * 1440)))
    grid = table._tbl.tblGrid
    for col, w in zip(grid.findall(qn("w:gridCol")), widths_in):
        col.set(qn("w:w"), str(int(w * 1440)))
    return table


def add_row(table, widths_in):
    row = table.add_row()
    for cell, w in zip(row.cells, widths_in):
        cell.width = Inches(w)
    return row


# ---------- shared page furniture ----------

def base_document(page_numbers=False, confidential=False):
    doc = Document()
    for p in list(doc.element.body.findall(qn("w:p"))):
        doc.element.body.remove(p)

    normal = doc.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(11)
    normal.font.color.rgb = TEXT
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.15

    for name, size, color, before, after in (
        ("Title", 24, INK, 0, 4),
        ("Heading 1", 16, INK, 18, 6),
        ("Heading 2", 13, INK, 14, 4),
    ):
        st = doc.styles[name]
        st.font.name = HEAD_FONT
        st.font.size = Pt(size)
        st.font.bold = False
        st.font.color.rgb = color
        rfonts = st.element.get_or_add_rPr().find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            st.element.get_or_add_rPr().append(rfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(attr), HEAD_FONT)
        for theme in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
            if rfonts.get(qn(theme)) is not None:
                del rfonts.attrib[qn(theme)]
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True
        ppr = st.element.get_or_add_pPr()
        for old in ppr.findall(qn("w:pBdr")):
            ppr.remove(old)

    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin = sec.right_margin = Inches(1)
    sec.top_margin = Inches(1.0)
    sec.bottom_margin = Inches(1.0)
    sec.header_distance = Inches(0.45)
    sec.footer_distance = Inches(0.45)

    # Header: logo, then a thin ink rule.
    hp = sec.header.paragraphs[0]
    spacing(hp, 0, 0)
    hp.add_run().add_picture(str(LOGO), width=Inches(3.1))
    rule = sec.header.add_paragraph()
    spacing(rule, 4, 14, line=1.0)
    set_font(rule.add_run(" "), size=2)
    border(rule, "top", INK_HEX, size=6, space=1)

    # Footer: thin rule, then address line (and optional extras).
    fp = sec.footer.paragraphs[0]
    spacing(fp, 0, 2, line=1.0)
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    border(fp, "top", LINE_HEX, size=6, space=8)
    parts = [
        f'{PRACTICE["street"]}, {PRACTICE["city"]}',
        PRACTICE["phone"],
        PRACTICE["email"],
        PRACTICE["web"],
    ]
    for i, part in enumerate(parts):
        if i:
            set_font(fp.add_run("   ·   "), size=8.5, color=CLAY)
        set_font(fp.add_run(part), size=8.5, color=STONE)
    if confidential:
        cp = sec.footer.add_paragraph()
        spacing(cp, 2, 0, line=1.0)
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(
            cp.add_run("Confidential: intended only for the person named. If you received this in error, please call the number above."),
            size=7.5, color=STONE, italic=True,
        )
    if page_numbers:
        pp = sec.footer.add_paragraph()
        spacing(pp, 2, 0, line=1.0)
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(pp.add_run("Page "), size=8.5, color=STONE)
        field(pp, "PAGE", size=8.5, color=STONE)
        set_font(pp.add_run(" of "), size=8.5, color=STONE)
        field(pp, "NUMPAGES", size=8.5, color=STONE)
    return doc


def para(doc, text="", size=None, color=None, bold=None, italic=None, before=0, after=8, font=BODY_FONT, align=None):
    p = doc.add_paragraph()
    spacing(p, before, after)
    if align is not None:
        p.alignment = align
    if text:
        set_font(p.add_run(text), name=font, size=size, color=color, bold=bold, italic=italic)
    return p


def label(doc, text, before=0, after=2):
    """Small clay uppercase label, like the eyebrows on the website."""
    p = doc.add_paragraph()
    spacing(p, before, after)
    run = set_font(p.add_run(text.upper()), size=8.5, color=CLAY, bold=True)
    run.font.spacing = Pt(1)
    return p


def signature(doc):
    para(doc, "Sincerely,", before=6, after=30)
    para(doc, PRACTICE["clinician"], bold=True, after=0)
    para(doc, PRACTICE["title"], color=STONE, after=0)
    para(doc, PRACTICE["name"], color=STONE, after=0)


# ---------- the four templates ----------

def letterhead():
    doc = base_document()
    para(doc, "")
    return doc


def client_letter():
    doc = base_document(confidential=True)
    para(doc, "[Month Day, Year]", after=18)
    para(doc, "[Recipient name]", after=0)
    para(doc, "[Street address]", after=0)
    para(doc, "[City, State ZIP]", after=18)
    p = para(doc, after=14)
    set_font(p.add_run("Re: "), bold=True, color=INK)
    set_font(p.add_run("[Subject of this letter]"))
    para(doc, "Dear [Name],", after=10)
    para(doc, "[Opening paragraph. Say why you are writing in one or two sentences.]")
    para(doc, "[Body paragraph. Give the details the reader needs.]")
    para(doc, "[Closing paragraph. Say what happens next and how to reach you with questions.]")
    signature(doc)
    return doc


def client_document():
    doc = base_document(page_numbers=True, confidential=True)
    label(doc, "[Document type, e.g. Practice policy]")
    doc.add_paragraph("[Document title]", style="Title")
    p = para(doc, after=16)
    set_font(p.add_run("Prepared for: "), color=STONE)
    set_font(p.add_run("[Client name]"))
    set_font(p.add_run("      Date: "), color=STONE)
    set_font(p.add_run("[Month Day, Year]"))
    para(doc, "[Introduction. A short paragraph on what this document covers and what, if anything, the client needs to do with it.]")
    doc.add_paragraph("[Section heading]", style="Heading 1")
    para(doc, "[Section text.]")
    for item in ("[First point]", "[Second point]", "[Third point]"):
        b = doc.add_paragraph(style="List Bullet")
        spacing(b, 0, 3)
        set_font(b.add_run(item))
    doc.add_paragraph("[Sub-heading]", style="Heading 2")
    para(doc, "[Supporting detail.]")
    doc.add_paragraph("[Section heading]", style="Heading 1")
    para(doc, "[Section text.]")
    doc.add_paragraph("Questions", style="Heading 1")
    para(doc, f'Call {PRACTICE["phone"]} or email {PRACTICE["email"]}. Please keep health details out of email.')
    return doc


def invoice():
    doc = base_document()
    # Title row: "Invoice" on the left, number and dates on the right.
    widths = [3.6, 2.9]
    head = fixed_table(doc, widths)
    row = add_row(head, widths)
    left, right = row.cells
    for c in row.cells:
        cell_fmt(c, borders={}, margins=(0, 108, 0, 108))
    lp = left.paragraphs[0]
    lp.style = doc.styles["Title"]
    lp.add_run("Invoice")
    sp = left.add_paragraph()
    spacing(sp, 0, 0)
    set_font(sp.add_run("[Invoice or Receipt: delete one]"), size=9, color=STONE, italic=True)
    first = True
    for name, value in (("Invoice no.", "[0000]"), ("Date", "[Month Day, Year]"), ("Due", "[Month Day, Year]")):
        rp = right.paragraphs[0] if first else right.add_paragraph()
        first = False
        spacing(rp, 0, 2)
        rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_font(rp.add_run(f"{name}  "), size=10, color=STONE)
        set_font(rp.add_run(value), size=10, bold=True)

    para(doc, "", after=6)

    # Bill to / From.
    widths = [3.25, 3.25]
    who = fixed_table(doc, widths)
    row = add_row(who, widths)
    for cell, heading, lines in (
        (row.cells[0], "Bill to", ["[Client name]", "[Street address]", "[City, State ZIP]"]),
        (row.cells[1], "From", [PRACTICE["clinician"], PRACTICE["name"], PRACTICE["street"], PRACTICE["city"]]),
    ):
        cell_fmt(cell, borders={"top": (INK_HEX, 12)}, margins=(110, 108, 60, 140))
        hp = cell.paragraphs[0]
        spacing(hp, 0, 3)
        r = set_font(hp.add_run(heading.upper()), size=8.5, color=CLAY, bold=True)
        r.font.spacing = Pt(1)
        for i, line in enumerate(lines):
            lp = cell.add_paragraph()
            spacing(lp, 0, 0)
            set_font(lp.add_run(line), size=10.5, bold=(i == 0))

    para(doc, "", after=8)

    # Line items.
    widths = [1.35, 3.75, 1.4]
    items = fixed_table(doc, widths)
    row = add_row(items, widths)
    for cell, text, align in zip(row.cells, ("Date of service", "Description", "Amount"),
                                 (None, None, WD_ALIGN_PARAGRAPH.RIGHT)):
        cell_fmt(cell, fill=INK_HEX, borders={})
        p = cell.paragraphs[0]
        spacing(p, 0, 0)
        if align:
            p.alignment = align
        set_font(p.add_run(text), size=9.5, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    samples = [("[MM/DD/YYYY]", "[Individual therapy session, 50 minutes]", "[$0.00]")] + [("", "", "")] * 4
    for date, desc, amount in samples:
        row = add_row(items, widths)
        for cell, text, align in zip(row.cells, (date, desc, amount), (None, None, WD_ALIGN_PARAGRAPH.RIGHT)):
            cell_fmt(cell, borders={"bottom": (LINE_HEX, 6)}, margins=(100, 110, 100, 110))
            p = cell.paragraphs[0]
            spacing(p, 0, 0)
            if align:
                p.alignment = align
            set_font(p.add_run(text), size=10.5)
    for name, value, strong in (("Total", "[$0.00]", False), ("Amount paid", "[$0.00]", False), ("Balance due", "[$0.00]", True)):
        row = add_row(items, widths)
        blank, lab, val = row.cells
        cell_fmt(blank, borders={})
        cell_fmt(lab, fill=TINT_HEX if strong else None, borders={})
        cell_fmt(val, fill=TINT_HEX if strong else None, borders={})
        p = lab.paragraphs[0]
        spacing(p, 0, 0)
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_font(p.add_run(name), size=10.5, bold=strong, color=INK if strong else STONE)
        p = val.paragraphs[0]
        spacing(p, 0, 0)
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_font(p.add_run(value), size=10.5, bold=strong)

    label(doc, "Payment", before=22)
    p = para(doc, after=2)
    set_font(p.add_run("Method: "), color=STONE)
    set_font(p.add_run("[Card / check / cash]"))
    set_font(p.add_run("      Received: "), color=STONE)
    set_font(p.add_run("[Month Day, Year]"))
    para(doc, f'Questions about this invoice? Call {PRACTICE["phone"]} or email {PRACTICE["email"]}.',
         size=10, color=STONE, before=14)
    para(doc, "Thank you.", font=HEAD_FONT, size=13, color=INK, before=4)
    return doc


TEMPLATES = {
    "JTBH Letterhead.docx": letterhead,
    "JTBH Client Letter.docx": client_letter,
    "JTBH Client Document.docx": client_document,
    "JTBH Invoice or Receipt.docx": invoice,
}

if __name__ == "__main__":
    for filename, build in TEMPLATES.items():
        build().save(str(HERE / filename))
        print("wrote", filename)
