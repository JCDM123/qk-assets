"""
parser.py — Cliniko letter text -> structured data  (V2)
Adds: [n] template-code detection from BODY (stripped from output, default 1),
name redundancy (subject-first with body fallback, both subject formats),
leftover-placeholder safety net, and certificate free-text capture for [3].
"""

import re

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
CODE_RE = re.compile(r"^[\s\u00a0]*\[\s*([0-9])\s*\][\s\u00a0]*$")
CODE_PREFIX_RE = re.compile(r"^[\s\u00a0]*\[\s*([0-9])\s*\][\s\u00a0]*")

SECTION_HEADERS = [
    "key points outlined",
    "dental findings",
    "osteopathic findings",
    "what is a cranial strain",
    "treatment plan",
]

# Leftover template placeholders that must never reach a family
PLACEHOLDER_STRINGS = [
    "PARENTS NAMES", "INSERT ", "FCC BULLET POINTS",
    "GUIDE TEMPLATE", "ALF TEMPLATE", "BULLET POINTS HERE",
]


def _clean(line):
    line = line.strip()
    line = re.sub(r"^[\u2022\u00b7\-\*]\s*", "", line)
    return line.strip()


def _collect_bullets(lines, start):
    bullets = []
    i = start
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j >= len(lines) or _is_header(lines[j]):
                break
            i += 1
            continue
        if _is_header(line):
            break
        bullets.append(_clean(line))
        i += 1
    return bullets, i


def _is_header(line):
    low = line.lower().strip().rstrip(":")
    return any(low.startswith(h) for h in SECTION_HEADERS)


def _extract_template_code(lines):
    """Find [n] at the START of any of the first body lines (alone on the line
    OR merged into a following line by email-client line-break rewriting,
    e.g. Outlook turning '[2]\nHEADING' into '[2] HEADING').
    Strips only the code; returns (code:int, cleaned_lines). Default 1."""
    for idx, line in enumerate(lines[:10]):
        if not line.strip():
            continue
        m = CODE_PREFIX_RE.match(line)
        if m:
            code = int(m.group(1))
            code = code if code in (1, 2, 3) else 1
            remainder = CODE_PREFIX_RE.sub("", line, count=1)
            if remainder.strip():
                cleaned = lines[:idx] + [remainder] + lines[idx + 1:]
            else:
                cleaned = lines[:idx] + lines[idx + 1:]
            return code, cleaned
        break  # only the first non-empty line may carry the code
    return 1, lines


def _check_placeholders(text):
    """Return list of leftover template placeholders found (safety net)."""
    found = []
    for p in PLACEHOLDER_STRINGS:
        if p in text:
            found.append(p)
    return found


def _name_from_subject(subject):
    """Full/first name from either subject format:
       'Letter for Vincent Casni'  or Cliniko auto 'Inaya - ...' """
    s = re.sub(r"^(re|fw|fwd)\s*:\s*", "", subject.strip(), flags=re.IGNORECASE)
    s = re.sub(r"^(re|fw|fwd)\s*:\s*", "", s, flags=re.IGNORECASE)  # nested RE: FW:
    m = re.search(r"(?:for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*$", s)
    if m:
        return m.group(1)
    m = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[-\u2013]", s)
    if m:
        return m.group(1).strip()
    return ""


def parse_cliniko_letter(body_text, subject="", clinic_domain="thequantumkid.com.au"):
    data = {
        "template": 1,
        "patient_full": "",
        "patient_first": "",
        "guardian": "",
        "date": "",
        "goals": [],
        "history": [],
        "dental": [],
        "osteo": [],
        "cranial_paragraphs": [],
        "treatment_lines": [],
        "practitioners": [],
        "patient_email": "",
        "cert_text": [],
        "flags": [],
    }

    text = body_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    # ── template code from body (stripped from output) ──
    data["template"], lines = _extract_template_code(lines)
    text = "\n".join(lines)

    # ── placeholder safety net ──
    data["flags"] = _check_placeholders(text)
    if data["flags"]:
        print(f"PIPELINE WARNING: leftover template placeholders found: "
              f"{data['flags']} — review before this reaches a family", flush=True)

    # ── patient email: first non-clinic address ──
    for m in EMAIL_RE.finditer(text):
        addr = m.group(0)
        if clinic_domain.lower() not in addr.lower() and "qkdental" not in addr.lower():
            data["patient_email"] = addr
            break

    # ── name redundancy: subject first ──
    if subject:
        subj_name = _name_from_subject(subject)
        if subj_name:
            data["patient_full"] = subj_name
            data["patient_first"] = subj_name.split()[0]

    # ── date ──
    for line in lines[:15]:
        m = re.search(r"\b(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})\b", line)
        if m:
            data["date"] = m.group(1)
            break

    # ── guardian ──
    m = re.search(r"^Dear\s+([^,\n]+),", text, re.MULTILINE)
    if m:
        data["guardian"] = m.group(1).strip()

    # ── patient first name: body fallback/confirmation ──
    m = re.search(r"opinion on\s+([A-Z][a-z]+)(?:'|\u2019)s\s+health goals", text)
    if m and not data["patient_first"]:
        data["patient_first"] = m.group(1)
    if not data["patient_full"] and data["patient_first"]:
        data["patient_full"] = data["patient_first"]

    # ── [3] certificate: free text = everything (code already stripped) ──
    if data["template"] == 3:
        skip = (data["date"],)
        cert = []
        for line in lines:
            s = line.strip()
            if not s or CODE_RE.match(s):
                if cert and cert[-1] != "":
                    cert.append("")
                continue
            if s in skip:
                continue
            cert.append(s)
        # merge into paragraphs on blank lines
        paras, buf = [], []
        for s in cert:
            if s == "":
                if buf:
                    paras.append(" ".join(buf))
                    buf = []
            else:
                buf.append(s)
        if buf:
            paras.append(" ".join(buf))
        data["cert_text"] = paras
        return data

    # ── goals ──
    in_goals = False
    for line in lines:
        s = line.strip()
        if "namely" in s.lower():
            in_goals = True
            continue
        if in_goals:
            m = re.match(r"^\d+[\.\)]\s*(.+)$", s)
            if m:
                data["goals"].append(m.group(1).strip())
            elif data["goals"] and s == "":
                continue
            elif data["goals"]:
                break

    # ── sections ──
    i = 0
    while i < len(lines):
        low = lines[i].lower().strip().rstrip(":")
        if low.startswith("key points outlined"):
            data["history"], i = _collect_bullets(lines, i + 1)
            continue
        if low.startswith("dental findings"):
            data["dental"], i = _collect_bullets(lines, i + 1)
            continue
        if low.startswith("osteopathic findings"):
            data["osteo"], i = _collect_bullets(lines, i + 1)
            continue
        if low.startswith("what is a cranial strain"):
            paras, buf = [], []
            j = i + 1
            while j < len(lines):
                s = lines[j].strip()
                if s.lower().startswith("treatment plan"):
                    break
                if s == "":
                    if buf:
                        paras.append(" ".join(buf))
                        buf = []
                else:
                    buf.append(s)
                j += 1
            if buf:
                paras.append(" ".join(buf))
            data["cranial_paragraphs"] = paras
            i = j
            continue
        if low.startswith("treatment plan"):
            data["treatment_lines"] = [l.rstrip() for l in lines[i + 1:]]
            break
        i += 1

    # ── practitioners ──
    for line in reversed(lines[-15:]):
        m = re.match(r"^([A-Z][A-Za-z\s]+?)\s*[-\u2013]\s*(Osteopath|Dentist|[A-Z][a-z]+)$",
                     line.strip())
        if m:
            data["practitioners"].insert(0, (m.group(1).strip(), m.group(2).strip()))

    return data
