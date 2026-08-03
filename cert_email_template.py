"""cert_email_template.py - joint-branded medical certificate email (template [3]+).

Styled as a certificate: framed block, patient name, PDF-attached note,
all three locations, dual website buttons. Doctor identity lives on the
attached PDF, not in this email.
"""
import html as _html

LOGO_URL = "https://raw.githubusercontent.com/JCDM123/qk-assets/main/cert_logo.png"
QK_SITE = "https://www.thequantumkid.com.au"
DENTAL_SITE = "https://www.qkdental.com.au"

LOCATIONS = [
    ("North Sydney", "0494 180 564", "northsydney@thequantumkid.com.au"),
    ("Byron Bay", "0494 180 564", "byronbay@thequantumkid.com.au"),
    ("QK Dental", "(02) 9923 2478", "hello@qkdental.com.au"),
]

def build_certificate_email(patient_first, guardian, patient_full):
    pf = _html.escape(patient_first or "your child")
    gd = _html.escape(guardian or "there")
    pfull = _html.escape(patient_full or patient_first or "the patient")
    P = "'Poppins','Century Gothic','Trebuchet MS',Arial,sans-serif"
    B = "Arial,Helvetica,sans-serif"
    BLUE = "#0075F6"
    ORANGE = "#F48C00"
    CREAM = "#EDEBDF"
    INK = "#2f3a4a"

    def loc_row(name, num, addr):
        tel = num.replace(" ", "").replace("(", "").replace(")", "")
        return f"""<tr>
          <td style="padding:9px 0;border-bottom:1px solid #dcd8c7;font-family:{B};">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
              <td style="font-size:14px;font-weight:bold;color:{INK};">{name}</td>
              <td align="right" style="font-size:13px;color:#5a5a5a;">
                <a href="tel:{tel}" style="color:{BLUE};text-decoration:none;">{num}</a>
                &nbsp;&middot;&nbsp;
                <a href="mailto:{addr}" style="color:{BLUE};text-decoration:none;">{addr}</a>
              </td>
            </tr></table>
          </td>
        </tr>"""

    loc_html = "".join(loc_row(n, p, a) for n, p, a in LOCATIONS)

    def site_btn(label, url):
        return f"""<td width="50%" align="center" valign="top" style="padding:6px;">
          <a href="{url}" style="display:block;background-color:{ORANGE};border-radius:8px;padding:13px 10px;font-family:{P};font-size:13px;font-weight:600;color:#ffffff;text-decoration:none;">{label}</a>
        </td>"""

    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
@media only screen and (max-width:600px){{.container{{width:100%!important;}}.px{{padding-left:24px!important;padding-right:24px!important;}}.stack{{display:block!important;width:100%!important;box-sizing:border-box;padding-bottom:10px!important;}}}}
a{{text-decoration:none;}}
</style></head>
<body style="margin:0;padding:0;background-color:#FFFFFF;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FFFFFF;">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background-color:{CREAM};border-radius:14px;overflow:hidden;">

  <tr><td align="center" style="padding:36px 44px 6px;">
    <img src="{LOGO_URL}" width="150" alt="The Quantum Kid" style="display:block;width:150px;height:auto;border:0;"/>
  </td></tr>

  <tr><td class="px" style="padding:24px 44px 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:2px solid {BLUE};border-radius:10px;background-color:#ffffff;">
      <tr><td align="center" style="padding:26px 30px 22px;">
        <div style="font-family:{P};font-size:24px;letter-spacing:4px;color:{INK};font-weight:400;margin-top:8px;">MEDICAL CERTIFICATE</div>
        <div style="width:60px;height:3px;background-color:{ORANGE};margin:14px auto 0;border-radius:2px;"></div>
        <p style="margin:20px 0 4px;font-family:{B};font-size:15px;line-height:1.7;color:#3a3a3a;">A medical certificate has been issued for</p>
        <p style="margin:0 0 6px;font-family:{P};font-size:22px;font-weight:600;color:{BLUE};">{pfull}</p>
        <p style="margin:8px 0 0;font-family:{B};font-size:14px;line-height:1.7;color:#5a5a5a;">The signed certificate is attached to this email as a PDF.</p>
      </td></tr>
    </table>
  </td></tr>

  <tr><td class="px" style="padding:26px 44px 6px;">
    <p style="margin:0 0 14px;font-family:{B};font-size:15px;line-height:1.7;color:#3a3a3a;">Dear {gd},</p>
    <p style="margin:0 0 14px;font-family:{B};font-size:15px;line-height:1.7;color:#3a3a3a;">Please find {pfull}'s medical certificate attached. If you have any questions, our team is happy to help at any of our locations below.</p>
  </td></tr>

  <tr><td class="px" style="padding:8px 44px 0;">
    <div style="font-family:{P};font-size:12px;letter-spacing:1.5px;color:{INK};font-weight:600;text-transform:uppercase;padding-bottom:4px;">Our Locations</div>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{loc_html}</table>
  </td></tr>

  <tr><td class="px" style="padding:22px 38px 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
      {site_btn("Visit The Quantum Kid", QK_SITE)}
      {site_btn("Visit QK Dental", DENTAL_SITE)}
    </tr></table>
  </td></tr>

  <tr><td align="center" style="padding:26px 44px 34px;"><div style="font-family:{B};font-size:12px;color:#999;line-height:1.6;">The Quantum Kid &middot; North Sydney &amp; Byron Bay &middot; QK Dental<br/>www.thequantumkid.com.au &middot; www.qkdental.com.au</div></td></tr>
</table></td></tr></table></body></html>"""
