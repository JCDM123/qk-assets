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

def _flow_css(bgs):
    """bgs: dict page_index -> b64 background. Build @page rules."""
    # margins: (top_mm, bottom_mm) per flow page index
    margins = {
        1: (38, 30),    # opening page: below big heading, above footer
        2: (14, 118),   # cranial imagery page: image from ~63%
        3: (14, 34),    # clean letterhead
        4: (14, 100),   # imagery B: image from ~70%
        5: (14, 34),    # clean
        6: (14, 100),   # imagery C: image from ~70%
        7: (14, 34),    # clean
    }
    rules = [f"""
@page {{ size: 210mm 297mm; margin: 14mm 12.2mm 34mm 12.2mm;
  background-image: url(data:image/png;base64,{bgs['clean']});
  background-size: 210mm 297mm; background-repeat:no-repeat;
  background-position: -12.2mm -14mm; }}"""]
    order = ['opening', 'cranial', 'clean', 'img_b', 'clean', 'img_c', 'clean']
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


def _build_flow_html(data, bgs):
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
            f'<style>{_flow_css(bgs)}</style></head><body>{body}</body></html>')


# ── clickable hotspot helper for the back page (coords from design, in mm) ──

def _hotspot(href, left, top, width, height):
    return (f'<a href="{href}" style="position:absolute; top:{top}mm; '
            f'left:{left}mm; width:{width}mm; height:{height}mm; '
            f'display:block;"></a>')


def generate_pdf(data, out_path):
    """data: dict from parser.parse_cliniko_letter; writes flow PDF to out_path."""
    a = lambda f: _b64(os.path.join(ASSETS, f))
    bgs = {
        "opening": a("page2_letter.png"),
        "cranial": a("page3_cranial.png"),
        "clean":   a("page4_treatment.png"),
        "img_b":   a("page_flow_b.png"),
        "img_c":   a("page_flow_c.png"),
    }
    cover_bg = a("page1_cover.png")
    quote_bg = a("page5_quote.png")
    back_bg = a("page_back_v3.png")

    first = data.get("patient_first", "")
    full = data.get("patient_full") or first

    # ── cover ──
    cover = _fixed_page(cover_bg, f"""
<div style="position:absolute; top:119mm; left:0; width:210mm; text-align:center;
     font-size:29pt; font-weight:700; color:{BLUE};">{_esc(full)}</div>""")

    # ── flowing content ──
    flow_html = _build_flow_html(data, bgs)
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
    back = _fixed_page(back_bg, "".join([
        _hotspot(URL_LINK,               60.4, 213.9, 84.6, 9.8),   # website
        _hotspot(f"tel:{PHONE}",         52.3, 262.2, 25.6, 7.3),   # NS phone
        _hotspot(f"mailto:{EMAIL_NS}",   52.3, 266.8, 65.9, 7.0),   # NS email
        _hotspot(f"tel:{PHONE}",        124.6, 262.2, 25.3, 7.3),   # BB phone
        _hotspot(f"mailto:{EMAIL_BB}",  124.6, 266.8, 60.6, 7.0),   # BB email
    ]))

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
