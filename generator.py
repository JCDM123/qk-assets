"""
generator.py — structured data -> branded Quantum Kid PDF  (V2 FLOW ENGINE)
Architecture: fixed cover -> flowing content (1-7 pages, scales with letter
length) -> fixed quote page -> fixed back page with clickable contacts.
Flow pages cycle through designed backgrounds via @page:nth() rules; text
never overlaps imagery or footers (per-page margins).
"""

import base64
import html
import os
import re
import warnings
from io import BytesIO

import weasyprint
from pypdf import PdfReader, PdfWriter

warnings.filterwarnings("ignore")

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

BLUE = "#0075F6"
ORANGE = "#F48C00"
DARK = "#231F20"

URL_LINK = "https://www.thequantumkid.com.au"
EMAIL_NS = "northsydney@thequantumkid.com.au"
EMAIL_BB = "byronbay@thequantumkid.com.au"
PHONE = "0494180564"

MAX_FLOW_PAGES = 7  # cover + 7 flow + quote + back = 10 max

# ── per-template skin configuration (multi-tenant pattern: template -> config) ──
SKINS = {
    1: {  # QK standard
        "assets": {"cover": "page1_cover.png", "opening": "page2_letter.png",
                   "img_a": "page3_cranial.png", "clean": "page4_treatment.png",
                   "img_b": "page_flow_b.png", "img_c": "page_flow_c.png",
                   "quote": "page5_quote.png", "back": "page_back_v3.png"},
        # bottom margins per flow page index (top is 38 for p1, 14 otherwise)
        "bottoms": {1: 30, 2: 118, 3: 34, 4: 100, 5: 34, 6: 100, 7: 34},
        "hotspots": [
            ("https://www.thequantumkid.com.au", 60.4, 213.9, 84.6, 9.8),
            ("tel:0494180564", 52.3, 262.2, 25.6, 7.3),
            ("mailto:northsydney@thequantumkid.com.au", 52.3, 266.8, 65.9, 7.0),
            ("tel:0494180564", 124.6, 262.2, 25.3, 7.3),
            ("mailto:byronbay@thequantumkid.com.au", 124.6, 266.8, 60.6, 7.0),
        ],
    },
    2: {  # QK Dental
        "assets": {"cover": "dental_01.png", "opening": "dental_02.png",
                   "img_a": "dental_03.png", "clean": "dental_04.png",
                   "img_b": "dental_05.png", "img_c": "dental_07.png",
                   "quote": "dental_09.png", "back": "dental_10.png"},
        "bottoms": {1: 30, 2: 85, 3: 34, 4: 95, 5: 34, 6: 103, 7: 34},
        "hotspots": [
            ("https://www.qkdental.com.au", 70.9, 214.8, 63.5, 7.8),
            ("tel:0299232478", 90.0, 258.9, 24.3, 5.0),
            ("mailto:hello@qkdental.com.au", 82.2, 263.2, 39.9, 5.3),
        ],
    },
}

CERT_LOGO = "cert_logo.png"
CERT_SIG = "cert_signature.png"
CERT_DATE_RE = re.compile(
    r"((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+)?"
    r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{4})")


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _esc(s):
    return html.escape(s, quote=False)


FONT_LINK = ('<link href="https://fonts.googleapis.com/css2'
             '?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet"/>')

# Shared text styles (same design system as V1)
TEXT_CSS = f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:Poppins,Arial,sans-serif;
  -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
p {{ font-size:10.5pt; line-height:1.55; color:{BLUE}; margin-bottom:4.2mm; font-weight:400; orphans:2; widows:2; }}
.keep {{ page-break-inside:avoid; }}
.head-orange {{ font-size:16pt; font-weight:700; color:{ORANGE}; margin:5.5mm 0 2.5mm;
  page-break-after:avoid; }}
.head-blue {{ font-size:14.5pt; font-weight:600; color:{BLUE}; margin:0 0 6mm;
  page-break-after:avoid; }}
.sub-blue {{ font-size:10.5pt; font-weight:600; color:{BLUE}; margin:4mm 0 1.5mm;
  page-break-after:avoid; }}
.doc-date {{ font-size:11.5pt; font-weight:700; color:{DARK}; margin-bottom:7mm; }}
ul {{ list-style:none; margin:0 0 4mm 0; }}
li {{ font-size:10.5pt; line-height:1.5; color:{BLUE}; padding-left:6mm; position:relative;
  margin-bottom:0.8mm; }}
li::before {{ content:"\\2022"; position:absolute; left:1.5mm; color:{BLUE}; opacity:0.6;
  font-size:9pt; top:0.7mm; }}
ol {{ list-style:none; margin:0 0 4mm 0; }}
ol li {{ padding-left:0; }}
ol li::before {{ content:none; }}
a {{ color:{BLUE}; text-decoration:none; }}
"""


# ── fixed single pages (cover / quote / back) use absolute layout like V1 ──

FIXED_CSS = f"""
@page {{ size: 210mm 297mm; margin: 0; }}
{TEXT_CSS}
body {{ width:210mm; height:297mm; overflow:hidden; }}
.bg {{ position:absolute; top:0; left:0; width:210mm; height:297mm; }}
"""


def _fixed_page(bg_b64, inner):
    return (f'<!DOCTYPE html><html><head><meta charset="UTF-8"/>{FONT_LINK}'
            f'<style>{FIXED_CSS}</style></head><body>'
            f'<img class="bg" src="data:image/png;base64,{bg_b64}"/>'
            f'{inner}</body></html>')


# ── the flow document: one HTML, content flows, backgrounds cycle ──
# Page rhythm: 1 opening -> 2 cranial imagery -> 3 clean -> 4 imagery B
#              -> 5 clean -> 6 imagery C -> 7 clean -> (8+ clean, warned)
# Bottom margins keep text clear of imagery / footers per page.

def _flow_css(bgs, bottoms):
    """bgs: dict key -> b64 background; bottoms: page idx -> bottom margin mm."""
    margins = {i: ((38 if i == 1 else 14), bottoms[i]) for i in range(1, 8)}
    rules = [f"""
@page {{ size: 210mm 297mm; margin: 14mm 12.2mm 34mm 12.2mm;
  background-image: url(data:image/png;base64,{bgs['clean']});
  background-size: 210mm 297mm; background-repeat:no-repeat;
  background-position: -12.2mm -14mm; }}"""]
    order = ['opening', 'img_a', 'clean', 'img_b', 'clean', 'img_c', 'clean']
    for i, key in enumerate(order, start=1):
        top, bottom = margins[i]
        rules.append(f"""
@page:nth({i}) {{ margin: {top}mm 12.2mm {bottom}mm 12.2mm;
  background-image: url(data:image/png;base64,{bgs[key]});
  background-size: 210mm 297mm; background-repeat:no-repeat;
  background-position: -12.2mm -{top}mm; }}""")
    return "\n".join(rules) + TEXT_CSS


def _bullets(items):
    return "".join(f"<li>{_esc(x)}</li>" for x in items)


def _treatment_html(lines):
    """Convert raw treatment-plan lines into styled HTML blocks.
    The closing block (from 'Thank you again...' to the end: sign-off names,
    'The Quantum Kid') is wrapped in a keep-together group so it can never
    split across pages and orphan a line onto its own page."""
    lines = list(lines)
    split_at = None
    for i, raw in enumerate(lines):
        if raw.strip().lower().startswith("thank you again"):
            split_at = i
            break
    if split_at is not None:
        head = _treatment_blocks(lines[:split_at])
        tail = _treatment_blocks(lines[split_at:])
        return head + f'<div class="keep">{tail}</div>'
    return _treatment_blocks(lines)


def _treatment_blocks(lines):
    out = []
    buf = []

    def flush_para():
        if buf:
            out.append(f"<p>{_esc(' '.join(buf))}</p>")
            buf.clear()

    in_list = False
    for raw in lines:
        s = raw.strip()
        if not s:
            if in_list:
                out.append("</ul>")
                in_list = False
            flush_para()
            continue
        if re.match(r"^\d+\.\s+[A-Z][a-z]+.*phase$", s, re.IGNORECASE):
            if in_list:
                out.append("</ul>")
                in_list = False
            flush_para()
            out.append(f'<div class="sub-blue">{_esc(s)}</div>')
            continue
        if re.match(r"^[\u2022\u00b7\-\*]\s+", s):
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_esc(re.sub(r'^[\u2022\u00b7\-\*]\s+', '', s))}</li>")
            continue
        if s.lower() == "the quantum kid":
            if in_list:
                out.append("</ul>")
                in_list = False
            flush_para()
            out.append(f'<p style="margin-bottom:0;font-weight:700;">{_esc(s)}</p>')
            continue
        if in_list:
            out[-1] = out[-1][:-5] + " " + _esc(s) + "</li>"
            continue
        buf.append(s)
    if in_list:
        out.append("</ul>")
    flush_para()
    return "\n".join(out)


def _section(title, items):
    """Orange-headed bullet section; renders only when content exists."""
    if not items:
        return ""
    return (f'<div class="head-orange">{title}</div>'
            f'<ul>{_bullets(items)}</ul>')


def _build_flow_html(data, bgs, bottoms):
    first = _esc(data.get("patient_first", ""))
    goals = "".join(f"<li>{i+1}. {_esc(g)}</li>"
                    for i, g in enumerate(data.get("goals", [])))
    parts = []
    if data.get("date"):
        parts.append(f'<div class="doc-date">{_esc(data["date"])}</div>')
    if data.get("guardian"):
        parts.append(f"<p>Dear {_esc(data['guardian'])},</p>")
    parts.append(
        f"<p>Thank you for visiting The Quantum Kid and entrusting us with an "
        f"opinion on {first}'s health goals, namely;</p>")
    if goals:
        parts.append(f"<ol>{goals}</ol>")
    parts.append(
        f"<p>{first} was a lovely young patient to have in the clinic and it "
        f"was great to hear about your family's journey to date.</p>")
    parts.append(_section(f"Key points outlined in {first}'s history:",
                          data.get("history", [])))
    parts.append(_section("Dental Findings:", data.get("dental", [])))
    parts.append(_section("Osteopathic Findings:", data.get("osteo", [])))
    if data.get("cranial_paragraphs"):
        parts.append(
            f'<div class="head-orange" style="text-transform:uppercase;">'
            f'Quantum Kid Program</div>'
            f'<div class="head-blue">What is a cranial strain?</div>')
        parts.extend(f"<p>{_esc(t)}</p>" for t in data["cranial_paragraphs"])
    if data.get("treatment_lines"):
        parts.append('<div class="head-orange">Treatment plan:</div>')
        parts.append(_treatment_html(data["treatment_lines"]))
    body = "\n".join(p for p in parts if p)
    return (f'<!DOCTYPE html><html><head><meta charset="UTF-8"/>{FONT_LINK}'
            f'<style>{_flow_css(bgs, bottoms)}</style></head><body>{body}</body></html>')


# ── clickable hotspot helper for the back page (coords from design, in mm) ──

def _hotspot(href, left, top, width, height):
    return (f'<a href="{href}" style="position:absolute; top:{top}mm; '
            f'left:{left}mm; width:{width}mm; height:{height}mm; '
            f'display:block;"></a>')


def generate_pdf(data, out_path):
    """data: dict from parser.parse_cliniko_letter; routes by data['template']."""
    template = data.get("template", 1)
    if template == 3:
        return generate_certificate(data, out_path)
    skin = SKINS.get(template, SKINS[1])
    a = lambda f: _b64(os.path.join(ASSETS, f))
    A = skin["assets"]
    bgs = {
        "opening": a(A["opening"]),
        "img_a":   a(A["img_a"]),
        "clean":   a(A["clean"]),
        "img_b":   a(A["img_b"]),
        "img_c":   a(A["img_c"]),
    }
    cover_bg = a(A["cover"])
    quote_bg = a(A["quote"])
    back_bg = a(A["back"])

    first = data.get("patient_first", "")
    full = data.get("patient_full") or first

    # ── cover ──
    cover = _fixed_page(cover_bg, f"""
<div style="position:absolute; top:119mm; left:0; width:210mm; text-align:center;
     font-size:29pt; font-weight:700; color:{BLUE};">{_esc(full)}</div>""")

    # ── flowing content ──
    flow_html = _build_flow_html(data, bgs, skin["bottoms"])
    flow_pdf = weasyprint.HTML(string=flow_html, base_url="/").write_pdf(
        presentational_hints=True)
    flow_reader = PdfReader(BytesIO(flow_pdf))
    n_flow = len(flow_reader.pages)
    if n_flow > MAX_FLOW_PAGES:
        print(f"PIPELINE WARNING: flow content used {n_flow} pages "
              f"(cap {MAX_FLOW_PAGES}) — letter unusually long, review output",
              flush=True)

    # ── quote page (artwork only) ──
    quote = _fixed_page(quote_bg, "")

    # ── back page: artwork + clickable contacts (coords from V3 design) ──
    back = _fixed_page(back_bg, "".join(
        _hotspot(href, x, y, w, h) for href, x, y, w, h in skin["hotspots"]))

    writer = PdfWriter()
    for html_page in (cover,):
        pdf = weasyprint.HTML(string=html_page, base_url="/").write_pdf(
            presentational_hints=True)
        writer.add_page(PdfReader(BytesIO(pdf)).pages[0])
    for pg in flow_reader.pages:
        writer.add_page(pg)
    for html_page in (quote, back):
        pdf = weasyprint.HTML(string=html_page, base_url="/").write_pdf(
            presentational_hints=True)
        writer.add_page(PdfReader(BytesIO(pdf)).pages[0])

    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path


# ── [3] Medical Certificate: single fixed A4, free text with auto-bolded dates ──

def _bold_dates(t):
    return CERT_DATE_RE.sub(lambda m: f"<b>{m.group(0)}</b>", _esc(t))


def generate_certificate(data, out_path):
    logo_b64 = _b64(os.path.join(ASSETS, CERT_LOGO))
    sig_b64 = _b64(os.path.join(ASSETS, CERT_SIG))
    name = _esc(data.get("patient_full") or data.get("patient_first") or "")
    issue = _esc(data.get("date", ""))
    paras = "".join(f"<p class='custom'>{_bold_dates(t)}</p>"
                    for t in data.get("cert_text", []))
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/>{FONT_LINK}
<style>
@page {{ size: 210mm 297mm; margin: 0; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:Poppins,Arial,sans-serif; width:210mm; height:297mm; overflow:hidden;
  background:#EDEBDF; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
.wrap {{ position:absolute; top:0; left:0; width:210mm; height:297mm; text-align:center; }}
.logo {{ margin-top:14mm; width:62mm; display:block; margin-left:auto; margin-right:auto; }}
.doctitle {{ margin-top:9mm; font-size:15pt; letter-spacing:4.5pt; color:{DARK};
  font-weight:400; text-transform:uppercase; }}
.rule {{ width:34mm; height:0.9mm; background:{ORANGE}; margin:8mm auto 0; border-radius:1mm; }}
.certify {{ margin-top:12mm; font-size:11.5pt; color:{DARK}; }}
.patient {{ margin-top:4mm; font-size:26pt; font-weight:700; color:{BLUE}; }}
.customblock {{ margin:9mm auto 0; width:138mm; text-align:center; }}
p.custom {{ font-size:11.5pt; color:{DARK}; line-height:1.8; margin-bottom:5mm; }}
p.custom b {{ font-weight:600; }}
.sigzone {{ position:absolute; bottom:46mm; left:0; width:210mm; text-align:center; }}
.sigimg {{ height:17mm; display:block; margin:0 auto 1.5mm; }}
.sigline {{ width:64mm; border-bottom:0.4mm solid {DARK}; margin:0 auto 2.5mm; }}
.signame {{ font-size:11.5pt; font-weight:600; color:{DARK}; }}
.sigrole {{ font-size:10pt; color:{DARK}; opacity:0.75; margin-top:1mm; }}
.ahpra {{ font-size:9pt; color:{DARK}; opacity:0.65; margin-top:1mm; }}
.issued {{ font-size:9.5pt; color:{DARK}; opacity:0.75; margin-top:4mm; }}
.footer {{ position:absolute; bottom:14mm; left:0; width:210mm; text-align:center;
  font-size:8.5pt; letter-spacing:1.8pt; color:{DARK}; opacity:0.55; text-transform:uppercase; }}
</style></head><body>
<div class="wrap">
  <img class="logo" src="data:image/png;base64,{logo_b64}"/>
  <div class="doctitle">Medical Certificate</div>
  <div class="rule"></div>
  <div class="certify">This is to certify that</div>
  <div class="patient">{name}</div>
  <div class="customblock">{paras}</div>
</div>
<div class="sigzone">
  <img class="sigimg" src="data:image/png;base64,{sig_b64}"/>
  <div class="sigline"></div>
  <div class="signame">Dr Jalal Khan</div>
  <div class="sigrole">Dentist</div>
  <div class="ahpra">AHPRA Registration: DEN0001234567</div>
  <div class="issued">Date of issue: {issue}</div>
</div>
<div class="footer">The Quantum Kid &middot; North Sydney &amp; Byron Bay &middot; www.thequantumkid.com.au</div>
</body></html>"""
    pdf = weasyprint.HTML(string=html, base_url="/").write_pdf(presentational_hints=True)
    with open(out_path, "wb") as f:
        f.write(pdf)
    return out_path
