"""Build reference.docx: the Word style sheet pandoc uses for kit documentation.

Arial, dark-blue headings (#1F3864), boxed tables, and a "To complete" paragraph
style shaded orange (#FCE4D6) for the parts the bank fills in.
Run: python3 tools/library/docs/make_reference_docx.py
"""
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

HERE = Path(__file__).parent
OUT = HERE / "reference.docx"
BLUE = RGBColor(0x1F, 0x38, 0x64)

subprocess.run(["pandoc", "-o", str(OUT), "--print-default-data-file", "reference.docx"], check=True)
doc = Document(OUT)


def font(style, size=None, bold=None, color=None, italic=None):
    f = style.font
    f.name = "Arial"
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(a), "Arial")
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if rfonts.get(qn(a)) is not None:
            del rfonts.attrib[qn(a)]
    if size:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color is not None:
        f.color.rgb = color


styles = doc.styles
S = {s.name: s for s in styles}  # pandoc uses UI names ("Heading 1") that python-docx lookups would remap
for name in ("Normal", "Body Text", "First Paragraph", "Compact", "Block Text"):
    if name in S:
        font(S[name], 10.5)
font(S["Title"], 22, True, BLUE)
for name, size in (("Heading 1", 15), ("Heading 2", 12.5), ("Heading 3", 11)):
    font(S[name], size, True, BLUE)
    S[name].paragraph_format.space_before = Pt(14 if name == "Heading 1" else 10)
    S[name].paragraph_format.space_after = Pt(4)

# "To complete": shaded paragraphs for bank-specific content
if "To complete" not in S:
    st = styles.add_style("To complete", WD_STYLE_TYPE.PARAGRAPH)
    st.base_style = S["Body Text"]
    font(st, 10.5, italic=True)
    ppr = st.element.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "FCE4D6")
    ppr.append(shd)

# Tables: thin grey borders on every cell, header row in light blue
tbl = S["Table"]
tpr = tbl.element.find(qn("w:tblPr"))
if tpr is None:
    tpr = OxmlElement("w:tblPr")
    tbl.element.append(tpr)
borders = OxmlElement("w:tblBorders")
for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
    b = OxmlElement(f"w:{side}")
    b.set(qn("w:val"), "single")
    b.set(qn("w:sz"), "4")
    b.set(qn("w:space"), "0")
    b.set(qn("w:color"), "A6B3C9")
    borders.append(b)
tpr.append(borders)
doc.save(OUT)
print("wrote", OUT)
