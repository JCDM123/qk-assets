"""email_template.py - branded landing email (robust buttons, text always visible)."""
import html as _html

HEADER_URL = "https://raw.githubusercontent.com/JCDM123/qk-assets/main/email-QKheader.png"
PAPERCLIP_URL = "https://raw.githubusercontent.com/JCDM123/qk-assets/main/paperclip_blue.png"
PHONE_ICON = "https://raw.githubusercontent.com/JCDM123/qk-assets/main/icon_phone_white.png"
MAIL_ICON = "https://raw.githubusercontent.com/JCDM123/qk-assets/main/icon_mail_blue.png"

def build_landing_email(patient_first, guardian, patient_full,
        website="https://www.thequantumkid.com.au",
        phone_ns="0494 180 564", phone_bb="0494 180 564",
        email_ns="northsydney@thequantumkid.com.au",
        email_bb="byronbay@thequantumkid.com.au"):
    pf = _html.escape(patient_first or "your child")
    gd = _html.escape(guardian or "there")
    pfull = _html.escape(patient_full or patient_first or "Patient")
    P = "'Poppins','Century Gothic','Trebuchet MS',Arial,sans-serif"
    B = "Arial,Helvetica,sans-serif"
    BLUE = "#0075F6"
    ORANGE = "#F48C00"

    def phone_btn(label, num):
        return f'''<td class="stack stack-pad" width="50%" valign="top" style="padding:6px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{BLUE};border-radius:8px;">
            <tr><td align="center" style="border-radius:8px;background-color:{BLUE};padding:11px 8px;font-family:{P};">
              <a href="tel:0494180564" style="text-decoration:none;display:block;">
                <img src="{PHONE_ICON}" width="14" height="14" alt="" style="vertical-align:middle;border:0;"/>&nbsp;<span style="color:#ffffff;font-size:13px;font-weight:600;">{label}</span><br/>
                <span style="color:#cfe5ff;font-size:12px;">{num}</span>
              </a>
            </td></tr>
          </table>
        </td>'''

    def email_btn(label, addr):
        return f'''<td class="stack stack-pad" width="50%" valign="top" style="padding:6px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1.5px solid {BLUE};border-radius:8px;">
            <tr><td align="center" style="border-radius:8px;padding:11px 8px;font-family:{P};">
              <a href="mailto:{addr}" style="text-decoration:none;display:block;">
                <img src="{MAIL_ICON}" width="14" height="11" alt="" style="vertical-align:middle;border:0;"/>&nbsp;<span style="color:{BLUE};font-size:12px;font-weight:600;">{label}</span>
              </a>
            </td></tr>
          </table>
        </td>'''

    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<!--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml><![endif]-->
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
@media only screen and (max-width:600px){{.container{{width:100%!important;}}.px{{padding-left:24px!important;padding-right:24px!important;}}.stack{{display:block!important;width:100%!important;box-sizing:border-box;}}.stack-pad{{padding-bottom:10px!important;}}.h1{{font-size:23px!important;}}}}
a{{text-decoration:none;}}
</style></head>
<body style="margin:0;padding:0;background-color:#FFFFFF;-webkit-text-size-adjust:100%;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FFFFFF;">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background-color:#EDEBDF;border-radius:14px;overflow:hidden;">
  <tr><td style="padding:0;"><img src="{HEADER_URL}" width="600" alt="The Quantum Kid" style="display:block;width:100%;max-width:600px;height:auto;border:0;"/></td></tr>
  <tr><td class="px" style="padding:30px 44px 0;">
    <h1 class="h1" style="margin:0 0 18px;font-family:{P};font-size:25px;font-weight:600;color:{BLUE};text-align:center;letter-spacing:0.3px;">{pf}'s Treatment Plan</h1>
    <p style="margin:0 0 16px;font-family:{B};font-size:15px;line-height:1.7;color:#3a3a3a;">Hi {gd},</p>
    <p style="margin:0 0 16px;font-family:{B};font-size:15px;line-height:1.7;color:#3a3a3a;">Thank you for trusting The Quantum Kid with {pf}'s care. We loved having you both in the clinic.</p>
    <p style="margin:0 0 26px;font-family:{B};font-size:15px;line-height:1.7;color:#3a3a3a;">{pf}'s personalised treatment plan is attached. Our Family Care Team will be in touch shortly with the next steps to get started.</p>
  </td></tr>
  <tr><td class="px" style="padding:0 44px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border:1px solid #e0ddd0;border-radius:10px;"><tr><td align="center" style="padding:22px;">
      <img src="{PAPERCLIP_URL}" width="28" height="28" alt="Attachment" style="display:block;margin:0 auto 10px auto;width:28px;height:28px;border:0;"/>
      <div style="font-family:{P};font-size:15px;font-weight:600;color:#231F20;">{pfull} - Treatment Plan.pdf</div>
      <div style="font-family:{B};font-size:13px;color:#888;margin-top:4px;">Your treatment plan is attached to this email</div>
    </td></tr></table>
  </td></tr>
  <tr><td class="px" style="padding:28px 44px 14px;"><div style="font-family:{B};font-size:13px;color:#888;text-align:center;">Please don't reply to this email. We'd love to hear from you here:</div></td></tr>
  <tr><td class="px" style="padding:0 38px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
    {phone_btn("North Sydney", phone_ns)}
    {phone_btn("Byron Bay", phone_bb)}
  </tr></table></td></tr>
  <tr><td class="px" style="padding:0 38px 8px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
    {email_btn("Email North Sydney", email_ns)}
    {email_btn("Email Byron Bay", email_bb)}
  </tr></table></td></tr>
  <tr><td align="center" style="padding:18px 44px 0;">
    <!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{website}" style="height:44px;v-text-anchor:middle;width:200px;" arcsize="18%" fillcolor="{ORANGE}" stroke="f"><center style="color:#ffffff;font-family:{B};font-size:14px;font-weight:bold;">Visit our website</center></v:roundrect><![endif]-->
    <!--[if !mso]><!-- -->
    <a href="{website}" style="display:inline-block;background-color:{ORANGE};border-radius:8px;padding:13px 34px;font-family:{P};font-size:14px;font-weight:600;color:#ffffff;text-decoration:none;">Visit our website</a>
    <!--<![endif]-->
  </td></tr>
  <tr><td align="center" style="padding:28px 44px 34px;"><div style="font-family:{B};font-size:12px;color:#999;line-height:1.6;">The Quantum Kid &middot; North Sydney &amp; Byron Bay<br/>www.thequantumkid.com.au</div></td></tr>
</table></td></tr></table></body></html>"""
