"""Generate QR artifacts and, optionally, an email-only copy of the supplied CV.

Requires Pillow, reportlab, and PyMuPDF. Website hosting has no dependencies.
Usage: python3 scripts/build_assets.py [--cv /path/to/source.pdf]
"""
from pathlib import Path
import argparse
import html
from PIL import Image, ImageDraw, ImageFont
from reportlab.graphics.barcode.qrencoder import QRCode, QRErrorCorrectLevel
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site" / "assets"
URL = "https://gwl0711.github.io/"


def qr_assets():
    qr = QRCode(None, QRErrorCorrectLevel.M)
    qr.addData(URL)
    qr.make()
    quiet = 4
    size = len(qr.modules) + quiet * 2
    squares = [(x + quiet, y + quiet) for y, row in enumerate(qr.modules)
               for x, black in enumerate(row) if black]
    paths = " ".join(f"M{x},{y}h1v1h-1z" for x, y in squares)
    (ASSETS / "qr-code.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size * 40}" height="{size * 40}" shape-rendering="crispEdges">'
        f'<title>{html.escape(URL)}</title><rect width="{size}" height="{size}" fill="white"/>'
        f'<path d="{paths}" fill="#18271e"/></svg>\n')
    scale = 40
    image = Image.new("RGB", (size * scale, size * scale), "white")
    draw = ImageDraw.Draw(image)
    for x, y in squares:
        draw.rectangle((x * scale, y * scale, (x + 1) * scale - 1,
                        (y + 1) * scale - 1), fill="#18271e")
    image.save(ASSETS / "qr-code.png", dpi=(300, 300))

    pdf = canvas.Canvas(str(ASSETS / "Gyuwon_Lee_QR.pdf"), pagesize=A4)
    pdf.setTitle("Gyuwon Lee — Conference QR")
    pdf.setAuthor("Gyuwon Lee")
    w, h = A4
    pdf.setFillColor(HexColor("#a84e34"))
    pdf.setFont("Courier", 10)
    pdf.drawCentredString(w / 2, h - 155, "NEURAL ENGINEERING & SPEECH BCI")
    pdf.setFillColor(HexColor("#26382f"))
    pdf.setFont("Times-Roman", 40)
    pdf.drawCentredString(w / 2, h - 215, "Gyuwon Lee")
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(w / 2, h - 245, "Let's continue the conversation.")
    module = 8
    x0, y0 = (w - size * module) / 2, h - 540
    pdf.setFillColor(HexColor("#18271e"))
    for x, y in squares:
        pdf.rect(x0 + x * module, y0 + (size - y - 1) * module,
                 module, module, stroke=0, fill=1)
    pdf.setFont("Courier", 15)
    pdf.drawCentredString(w / 2, y0 - 24, "gwl0711.github.io")
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(w / 2, y0 - 52, "Research  /  Publications  /  CV  /  Contact")
    pdf.linkURL(URL, (x0, y0, x0 + size * module, y0 + size * module), relative=0)
    pdf.save()


def public_cv(source):
    import fitz
    document = fitz.open(source)
    page = document[0]
    phone_line = None
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(span["text"] for span in line["spans"])
            if "Email:" in text and "Phone:" in text:
                phone_line = fitz.Rect(line["bbox"])
                break
    if phone_line is None:
        raise ValueError("Expected contact header not found; inspect CV before publishing")
    page.add_redact_annot(phone_line, fill=(1, 1, 1))
    page.apply_redactions()
    email = "Email: gwl0711@gmail.com"
    width = fitz.get_text_length(email, fontname="helv", fontsize=10)
    page.insert_text(((page.rect.width - width) / 2, phone_line.y1 - 2.5),
                     email, fontname="helv", fontsize=10, color=(.13, .13, .13))
    # Correct the source CV's abbreviated author list against the publisher.
    # Only replace the known older citation; a future corrected CV is left alone.
    for citation_page in document:
        old_author_line = citation_page.search_for('Kwon, J.*, Lee, G.*, & Chung, C.K. (2025).')
        if not old_author_line:
            continue
        doi_line = citation_page.search_for('https://doi.org/10.1038/s41598-025-18537-2')
        if not doi_line:
            raise ValueError('Cannot locate the end of the citation to correct')
        box = fitz.Rect(36, old_author_line[0].y0 - .5, citation_page.rect.width - 36,
                        doi_line[0].y1 + .5)
        citation_page.add_redact_annot(box, fill=(1, 1, 1))
        citation_page.apply_redactions()
        citation = ('Kwon, J.*, <b>Lee, G.*</b>, Park, Y. J., Lee, E. J., &amp; Chung, C. K. (2025). '
                    '“Mimed speech as an intermediary state between overt and imagined speech production '
                    'in an electrocorticography study”. <i>Scientific Reports, 15</i>, 33393. '
                    '<a href="https://doi.org/10.1038/s41598-025-18537-2">'
                    'https://doi.org/10.1038/s41598-025-18537-2</a>')
        spare, scale = citation_page.insert_htmlbox(box, citation,
                         css='* {font-family: serif; font-size: 11pt; line-height: 1.12;} body {margin:0;} a {color: #222; text-decoration: none;}',
                         scale_low=.9)
        if spare < 0:
            raise ValueError('Corrected citation does not fit; inspect the public CV')
    document.set_metadata({"title": "Gyuwon Lee — Curriculum Vitae", "author": "Gyuwon Lee"})
    document.save(ASSETS / "Gyuwon_Lee_CV.pdf", garbage=4, deflate=True)
    document.close()
    with fitz.open(ASSETS / "Gyuwon_Lee_CV.pdf") as check:
        text = "".join(page.get_text() for page in check)
        assert "Phone:" not in text and "+82-10" not in text
        assert "gwl0711@gmail.com" in text
        assert "Park, Y. J., Lee, E. J." in text


def social_card():
    image = Image.new("RGB", (1200, 630), "#f8f7f3")
    draw = ImageDraw.Draw(image)
    fonts = Path("/usr/share/fonts/truetype")
    serif = fonts / "msttcorefonts" / "Georgia.ttf"
    if not serif.exists():
        serif = fonts / "dejavu" / "DejaVuSerif.ttf"
    sans = fonts / "dejavu" / "DejaVuSans.ttf"
    mono = fonts / "dejavu" / "DejaVuSansMono.ttf"
    draw.text((75, 82), "NEURAL ENGINEERING & SPEECH BCI", fill="#a84e34",
              font=ImageFont.truetype(str(mono), 18))
    draw.text((70, 149), "Gyuwon Lee", fill="#26382f",
              font=ImageFont.truetype(str(serif), 82))
    draw.text((75, 284), "Understanding neural dynamics.", fill="#26382f",
              font=ImageFont.truetype(str(serif), 31))
    draw.text((75, 331), "Building toward communication.", fill="#a84e34",
              font=ImageFont.truetype(str(serif), 31))
    draw.text((75, 421), "NICA Lab · Konkuk University Medical Center", fill="#657168",
              font=ImageFont.truetype(str(sans), 18))
    draw.line((75, 500, 1125, 500), fill="#dadfd6", width=2)
    draw.text((75, 539), "gwl0711.github.io", fill="#657168",
              font=ImageFont.truetype(str(mono), 19))
    portrait = Image.open(ASSETS / "portrait-gyuwon-lee.jpg").convert("RGB")
    portrait.thumbnail((250, 320))
    draw.rectangle((830, 105, 1128, 457), fill="#e9ece4")
    image.paste(portrait, (854, 125))
    draw.text((854, 394), "From neural signals", fill="#53634f",
              font=ImageFont.truetype(str(serif), 17))
    draw.text((854, 419), "to human connection.", fill="#53634f",
              font=ImageFont.truetype(str(serif), 17))
    image.save(ASSETS / "social-card-portrait.png", optimize=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cv", type=Path)
    args = parser.parse_args()
    ASSETS.mkdir(parents=True, exist_ok=True)
    qr_assets()
    social_card()
    if args.cv:
        public_cv(args.cv)
    print("Generated QR (SVG, PNG, PDF), social preview" + (", public CV" if args.cv else ""))
