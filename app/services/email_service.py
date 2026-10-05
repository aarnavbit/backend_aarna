import smtplib
from email.mime.text import MIMEText
try:
    import resend
except ImportError:
    resend = None
from app.config import settings


class EmailAdapter:
    def send(self, to: str, subject: str, html_body: str):
        raise NotImplementedError


class ResendAdapter(EmailAdapter):
    def send(self, to: str, subject: str, html_body: str):
        global resend
        if not settings.RESEND_API_KEY:
            print(f"[EMAIL] Resend API key not configured, skipping email to {to}: {subject}")
            return None

        if resend is None:
            try:
                import resend as _resend
                resend = _resend
            except ImportError:
                print(f"[EMAIL] resend package is not installed; skipping email to {to}: {subject}")
                return None

        from_email = settings.RESEND_FROM_EMAIL or "onboarding@resend.dev"
        try:
            resend.api_key = settings.RESEND_API_KEY
            params = {
                "from": from_email,
                "to": to,
                "subject": subject,
                "html": html_body,
            }
            response = resend.Emails.send(params)
            email_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", "sent")
            print(f"[EMAIL] Sent via Resend to {to}: {subject} (ID: {email_id})")
            return response
        except Exception as e:
            err_msg = str(e)
            print(f"[EMAIL] Failed to send via Resend to {to}: {err_msg}")

            # If using Resend sandbox testing domain (onboarding@resend.dev), Resend blocks external recipients.
            # Deliver a notification copy to the verified account owner so the admin is immediately alerted!
            if "onboarding@resend.dev" in from_email and "only send testing emails" in err_msg.lower():
                fallback_owner = "aarnavbit@gmail.com"
                if to.lower() != fallback_owner.lower():
                    try:
                        print(f"[EMAIL SANDBOX] Resend testing domain restricted to account owner. Forwarding notification for {to} to {fallback_owner}")
                        sandbox_notice = f"""
                        <div style="padding:14px;background:#fef3c7;border:1px solid #f59e0b;border-radius:8px;margin-bottom:18px;font-family:Arial,sans-serif;color:#92400e;font-size:14px;">
                            <strong>⚠️ Resend Sandbox Mode Notice:</strong><br/>
                            This email was addressed to <strong>{to}</strong>.<br/>
                            Because <code>onboarding@resend.dev</code> is a testing domain, Resend only delivers to your registered account (<code>{fallback_owner}</code>).<br/>
                            👉 To deliver directly to applicant inboxes, verify your domain at <a href="https://resend.com/domains" style="color:#b45309;font-weight:bold;">resend.com/domains</a>.
                        </div>
                        """
                        fallback_params = {
                            "from": from_email,
                            "to": fallback_owner,
                            "subject": f"[Sandbox Copy for {to}] {subject}",
                            "html": sandbox_notice + html_body,
                        }
                        fb_resp = resend.Emails.send(fallback_params)
                        fb_id = fb_resp.get("id") if isinstance(fb_resp, dict) else getattr(fb_resp, "id", "sent")
                        print(f"[EMAIL] Sandbox fallback copy delivered to {fallback_owner} (ID: {fb_id})")
                        return fb_resp
                    except Exception as fb_err:
                        print(f"[EMAIL] Sandbox fallback failed: {fb_err}")

            return None


class SMTPAdapter(EmailAdapter):
    def send(self, to: str, subject: str, html_body: str):
        if not settings.ISHANYA_SMTP_USER or not settings.ISHANYA_SMTP_PASS:
            print(f"[EMAIL] SMTP not configured, skipping email to {to}: {subject}")
            return None

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.ISHANYA_EMAIL_FROM
            msg["To"] = to
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.ISHANYA_SMTP_HOST, settings.ISHANYA_SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(settings.ISHANYA_SMTP_USER, settings.ISHANYA_SMTP_PASS)
                server.sendmail(settings.ISHANYA_EMAIL_FROM, to, msg.as_string())

            print(f"[EMAIL] Sent via SMTP to {to}: {subject}")
        except Exception as e:
            print(f"[EMAIL] Failed to send via SMTP to {to}: {e}")
            return None


def get_email_adapter() -> EmailAdapter:
    if settings.RESEND_API_KEY:
        return ResendAdapter()
    return SMTPAdapter()


def send_test_email(to: str = "aarnavbit@gmail.com"):
    """Sends the first test email via Resend API."""
    adapter = ResendAdapter()
    subject = "Hello World"
    html_body = "<p>Congrats on sending your <strong>first email</strong>!</p>"
    return adapter.send(to=to, subject=subject, html_body=html_body)


ISHANYA_ACCEPTANCE_EMAIL_TEMPLATE = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="x-apple-disable-message-reformatting" />
  <meta name="format-detection" content="telephone=no, date=no, address=no, email=no" />
  <title>Registration Confirmed for ISHANYA'26 | Team AARNA</title>
  <style type="text/css">
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Quicksand:wght@600;700;800&display=swap');

    body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }
    table, td { mso-table-lspace: 0pt; mso-table-rspace: 0pt; }
    img { -ms-interpolation-mode: bicubic; border: 0; height: auto; line-height: 100%; outline: none; text-decoration: none; }
    table { border-collapse: separate !important; }
    body { height: 100% !important; margin: 0 !important; padding: 0 !important; width: 100% !important; background-color: #fbeee0; }

    .btn-wa:hover {
      background-color: #20bd5a !important;
      transform: translateY(-2px);
    }
    .track-card:hover {
      transform: translateY(-1px);
    }

    @media only screen and (max-width: 600px) {
      .email-wrapper {
        padding: 12px 8px !important;
      }
      .email-card {
        border-radius: 20px !important;
        width: 100% !important;
      }
      .card-content {
        padding: 24px 18px !important;
      }
      .hero-title {
        font-size: 24px !important;
        line-height: 30px !important;
      }
      .detail-label {
        width: 100% !important;
        display: block !important;
        padding-bottom: 2px !important;
      }
      .detail-value {
        width: 100% !important;
        display: block !important;
        padding-bottom: 12px !important;
      }
      .logo-img {
        max-width: 250px !important;
      }
      .track-grid-cell {
        display: block !important;
        width: 100% !important;
        padding: 0 0 8px 0 !important;
      }
    }
  </style>
</head>
<body bgcolor="#fbeee0" style="margin: 0; padding: 0; background-color: #fbeee0; font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #3b2412;">

  <!-- Outer background container -->
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="email-wrapper" bgcolor="#fbeee0" style="background-color: #fbeee0; padding: 32px 12px;">
    <tr>
      <td align="center" valign="top">

        <!-- Preheader hidden snippet text (Inbox snippet) -->
        <div style="display: none; font-size: 1px; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden; mso-hide: all;">
          🎉 Congratulations! Your registration is confirmed for ISHANYA'26. View your event pass, venue details, and track info inside.
          &#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;
        </div>

        <!-- Main Card Container (600px max width) -->
        <!--[if (gte mso 9)|(IE)]>
        <table align="center" border="0" cellspacing="0" cellpadding="0" width="600" style="width: 600px;">
        <tr>
        <td align="center" valign="top" width="600" style="width: 600px;">
        <![endif]-->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="email-card" style="max-width: 600px; background-color: #ffffff; border-radius: 24px; border: 3px solid #3b2412; box-shadow: 6px 6px 0px #3b2412; overflow: hidden;">
          
          <!-- Top Decorative Rainbow Gradient Accent Bar -->
          <tr>
            <td bgcolor="#c9aef0" style="background: linear-gradient(90deg, #c9aef0 0%, #f4795b 50%, #c9aef0 100%); height: 10px; font-size: 0; line-height: 0; border-bottom: 2px solid #3b2412;">
              &nbsp;
            </td>
          </tr>

          <!-- Header / Club Branding -->
          <tr>
            <td align="center" style="padding: 24px 24px 16px 24px; border-bottom: 2px dashed #e8d9cc;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <!-- Club Logo -->
                  <td valign="middle" style="padding-right: 12px;">
                    <img src="https://raw.githubusercontent.com/aarnavbit/frontend_aarna/main/public/Logo.png" alt="AARNA Logo" width="46" height="46" style="display: block; border-radius: 10px; border: 2px solid #3b2412;" />
                  </td>
                  <!-- Club Name & Subtitle -->
                  <td valign="middle" align="left">
                    <div style="font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 20px; font-weight: 800; letter-spacing: 0.08em; color: #3b2412; line-height: 22px;">
                      AARNA
                    </div>
                    <div style="font-family: 'Poppins', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 0.06em; color: #9c7655; text-transform: uppercase; line-height: 14px;">
                      FREELANCING CLUB &bull; TURNING PASSIONS INTO PROFITS
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Content Area -->
          <tr>
            <td class="card-content" style="padding: 30px 28px 24px 28px; text-align: left;">

              <!-- Badges Row -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 18px;">
                    <div style="display: inline-block; background-color: #c9aef0; border: 2px solid #3b2412; border-radius: 50px; padding: 5px 16px; box-shadow: 2px 2px 0px #3b2412; margin-right: 6px; margin-bottom: 6px;">
                      <span style="font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 11px; font-weight: 800; letter-spacing: 0.08em; color: #3b2412; text-transform: uppercase;">
                        ⚡ FLAGSHIP EVENT · ISHANYA '26
                      </span>
                    </div>
                    <div style="display: inline-block; background-color: #dcfce7; border: 2px solid #16a34a; border-radius: 50px; padding: 5px 14px; box-shadow: 2px 2px 0px #16a34a; margin-bottom: 6px;">
                      <span style="font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 11px; font-weight: 800; letter-spacing: 0.05em; color: #15803d; text-transform: uppercase;">
                        ACCEPTED &amp; CONFIRMED &#10004;
                      </span>
                    </div>
                  </td>
                </tr>

                <!-- Event Brand Logo Banner -->
                <tr>
                  <td align="center" style="padding-bottom: 16px;">
                    <img src="https://raw.githubusercontent.com/aarnavbit/frontend_aarna/main/public/images/ishanya_logo.png" alt="Ishanya '26 - Visualize. Create. Inspire." class="logo-img" width="290" style="max-width: 290px; width: 80%; height: auto; display: block;" />
                  </td>
                </tr>

                <!-- Congratulations Headline -->
                <tr>
                  <td align="center" style="padding-bottom: 8px;">
                    <h1 class="hero-title" style="margin: 0; font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 26px; line-height: 32px; font-weight: 800; color: #3b2412; letter-spacing: -0.02em;">
                      &#127881; Congratulations!
                    </h1>
                  </td>
                </tr>

                <!-- Greetings & Confirmation Subtitle -->
                <tr>
                  <td align="center" style="padding-bottom: 22px;">
                    <p style="margin: 0 0 6px 0; font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 16px; font-weight: 800; color: #f4795b; letter-spacing: 0.02em;">
                      Greetings from Team AARNA 2K26!
                    </p>
                    <p style="margin: 0 0 8px 0; font-family: 'Poppins', sans-serif; font-size: 15px; font-weight: 700; color: #3b2412;">
                      You're registration confirmed for <span style="background-color: #c9aef0; padding: 2px 8px; border-radius: 6px; border: 1.5px solid #3b2412; display: inline-block;">ISHANYA'26</span>!
                    </p>
                    <p style="margin: 0; font-family: 'Poppins', sans-serif; font-size: 14px; line-height: 22px; color: #6e4a2d; max-width: 490px;">
                      We're glad to have you on board &mdash; here's everything you need to know before the day.
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Digital Entry Pass Card (Neo-Brutalist Pass) -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #fbeee0; border-radius: 18px; border: 2.5px solid #3b2412; box-shadow: 4px 4px 0px #3b2412; margin-bottom: 24px; overflow: hidden;">
                <tr>
                  <!-- Card Header Bar -->
                  <td bgcolor="#f4795b" style="background-color: #f4795b; padding: 9px 16px; border-bottom: 2px solid #3b2412;">
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td align="left">
                          <span style="font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 11px; font-weight: 800; letter-spacing: 0.07em; color: #ffffff; text-transform: uppercase;">
                            &#127915; OFFICIAL EVENT ENTRY PASS
                          </span>
                        </td>
                        <td align="right">
                          <span style="font-family: 'Poppins', sans-serif; font-size: 10px; font-weight: 700; color: #ffffff; background-color: #3b2412; padding: 2px 8px; border-radius: 10px; letter-spacing: 0.05em;">
                            VERIFIED
                          </span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 16px 20px;">
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                      <!-- Event Name -->
                      <tr>
                        <td class="detail-label" valign="middle" style="padding: 6px 0; width: 135px; font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 600; color: #9c7655;">
                          Event Name:
                        </td>
                        <td class="detail-value" valign="middle" style="padding: 6px 0; font-family: 'Poppins', sans-serif; font-size: 14px; font-weight: 800; color: #3b2412;">
                          Ishanya '26 &bull; <span style="font-weight: 600; color: #6e4a2d; font-size: 12px;">Visualize. Create. Inspire.</span>
                        </td>
                      </tr>
                      <!-- Team Name -->
                      <tr>
                        <td class="detail-label" valign="middle" style="padding: 6px 0; width: 135px; font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 600; color: #9c7655; border-top: 1px dashed #e8d9cc;">
                          Team Name:
                        </td>
                        <td class="detail-value" valign="middle" style="padding: 6px 0; font-family: 'Poppins', sans-serif; font-size: 15px; font-weight: 800; color: #3b2412; border-top: 1px dashed #e8d9cc;">
                          {team_name}
                        </td>
                      </tr>
                      <!-- Registration ID -->
                      <tr>
                        <td class="detail-label" valign="middle" style="padding: 6px 0; width: 135px; font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 600; color: #9c7655; border-top: 1px dashed #e8d9cc;">
                          Registration ID:
                        </td>
                        <td class="detail-value" valign="middle" style="padding: 6px 0; border-top: 1px dashed #e8d9cc;">
                          <code style="background-color: #ffffff; border: 1.5px solid #3b2412; border-radius: 6px; padding: 3px 10px; font-family: 'Courier New', Courier, monospace; font-size: 14px; font-weight: 800; color: #3b2412; letter-spacing: 0.05em; display: inline-block;">
                            {registration_id}
                          </code>
                        </td>
                      </tr>
                      <!-- Status -->
                      <tr>
                        <td class="detail-label" valign="middle" style="padding: 6px 0; width: 135px; font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 600; color: #9c7655; border-top: 1px dashed #e8d9cc;">
                          Status:
                        </td>
                        <td class="detail-value" valign="middle" style="padding: 6px 0; border-top: 1px dashed #e8d9cc;">
                          <span style="font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 800; color: #15803d;">
                            &#9989; Accepted &amp; Slot Allocated
                          </span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Tracks Overview Section -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px;">
                <tr>
                  <td>
                    <p style="margin: 0 0 10px 0; font-family: 'Poppins', sans-serif; font-size: 14px; line-height: 22px; color: #3b2412;">
                      <strong>Get ready to put your skills to work.</strong> ISHANYA'26 brings together three tracks &mdash; <strong>Designing</strong>, <strong>Video Editing / Media</strong>, and <strong>AI &amp; Marketing Automation</strong> &mdash; where you'll receive a real brief, work under a deadline, and deliver your best work.
                    </p>
                  </td>
                </tr>
                <tr>
                  <td>
                    <!-- 3 Track Feature Pills -->
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <!-- Track 1: Designing -->
                        <td class="track-grid-cell" width="32%" valign="top" style="padding: 0 4px 6px 0;">
                          <div style="background-color: #ffffff; border: 2px solid #3b2412; border-radius: 12px; padding: 10px 8px; text-align: center; box-shadow: 2px 2px 0px #3b2412;">
                            <div style="font-size: 18px; margin-bottom: 4px;">&#127912;</div>
                            <div style="font-family: 'Quicksand', sans-serif; font-size: 12px; font-weight: 800; color: #3b2412; text-transform: uppercase;">Designing</div>
                            <div style="font-family: 'Poppins', sans-serif; font-size: 10.5px; color: #6e4a2d; margin-top: 2px;">UI/UX &bull; Graphics</div>
                          </div>
                        </td>
                        <!-- Track 2: Video Editing / Media -->
                        <td class="track-grid-cell" width="34%" valign="top" style="padding: 0 3px 6px 3px;">
                          <div style="background-color: #ffffff; border: 2px solid #3b2412; border-radius: 12px; padding: 10px 8px; text-align: center; box-shadow: 2px 2px 0px #3b2412;">
                            <div style="font-size: 18px; margin-bottom: 4px;">&#127916;</div>
                            <div style="font-family: 'Quicksand', sans-serif; font-size: 12px; font-weight: 800; color: #3b2412; text-transform: uppercase;">Video / Media</div>
                            <div style="font-family: 'Poppins', sans-serif; font-size: 10.5px; color: #6e4a2d; margin-top: 2px;">Reels &bull; Visuals</div>
                          </div>
                        </td>
                        <!-- Track 3: AI & Marketing Automation -->
                        <td class="track-grid-cell" width="34%" valign="top" style="padding: 0 0 6px 4px;">
                          <div style="background-color: #ffffff; border: 2px solid #3b2412; border-radius: 12px; padding: 10px 8px; text-align: center; box-shadow: 2px 2px 0px #3b2412;">
                            <div style="font-size: 18px; margin-bottom: 4px;">&#129302;</div>
                            <div style="font-family: 'Quicksand', sans-serif; font-size: 12px; font-weight: 800; color: #3b2412; text-transform: uppercase;">AI &amp; Marketing</div>
                            <div style="font-family: 'Poppins', sans-serif; font-size: 10.5px; color: #6e4a2d; margin-top: 2px;">Automation &bull; Growth</div>
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Motto Tagline Box -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 18px;">
                <tr>
                  <td align="center" bgcolor="#fbeee0" style="background-color: #fbeee0; border-radius: 12px; border: 1.5px dashed #f4795b; padding: 10px 16px;">
                    <p style="margin: 0; font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 15px; font-weight: 800; color: #f4795b; letter-spacing: 0.05em; text-transform: uppercase;">
                      &ldquo;Visualize. Create. Inspire.&rdquo;
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Our Approach Pipeline Box -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border: 2px solid #3b2412; border-radius: 14px; padding: 12px 14px; box-shadow: 3px 3px 0px #3b2412; margin-bottom: 22px;">
                <tr>
                  <td style="padding-bottom: 8px;">
                    <span style="font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 12px; font-weight: 800; color: #3b2412; text-transform: uppercase; letter-spacing: 0.05em;">
                      &#9881;&#65039; Our Approach:
                    </span>
                  </td>
                </tr>
                <tr>
                  <td align="center">
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td align="center" style="font-family: 'Poppins', sans-serif; font-size: 12px; font-weight: 700; color: #3b2412; line-height: 20px;">
                          <span style="background-color: #fbeee0; border: 1.5px solid #3b2412; border-radius: 6px; padding: 3px 8px; display: inline-block; margin: 2px;">Brief</span>
                          <span style="color: #f4795b; font-weight: 800; margin: 0 2px;">&rarr;</span>
                          <span style="background-color: #c9aef0; border: 1.5px solid #3b2412; border-radius: 6px; padding: 3px 8px; display: inline-block; margin: 2px;">Think</span>
                          <span style="color: #f4795b; font-weight: 800; margin: 0 2px;">&rarr;</span>
                          <span style="background-color: #fed7aa; border: 1.5px solid #3b2412; border-radius: 6px; padding: 3px 8px; display: inline-block; margin: 2px;">Create</span>
                          <span style="color: #f4795b; font-weight: 800; margin: 0 2px;">&rarr;</span>
                          <span style="background-color: #fef08a; border: 1.5px solid #3b2412; border-radius: 6px; padding: 3px 8px; display: inline-block; margin: 2px;">Execute</span>
                          <span style="color: #f4795b; font-weight: 800; margin: 0 2px;">&rarr;</span>
                          <span style="background-color: #bbf7d0; border: 1.5px solid #3b2412; border-radius: 6px; padding: 3px 8px; display: inline-block; margin: 2px;">Deliver</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Event Details Card -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #fbeee0; border-radius: 16px; border: 2px solid #3b2412; box-shadow: 4px 4px 0px #3b2412; margin-bottom: 22px; overflow: hidden;">
                <tr>
                  <td bgcolor="#c9aef0" style="background-color: #c9aef0; padding: 9px 16px; border-bottom: 2px solid #3b2412;">
                    <span style="font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 12px; font-weight: 800; letter-spacing: 0.06em; color: #3b2412; text-transform: uppercase;">
                      &#128197; Event Details
                    </span>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 14px 18px;">
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                      <!-- Date -->
                      <tr>
                        <td width="90" valign="top" style="padding: 5px 0; font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 700; color: #9c7655;">
                          Date:
                        </td>
                        <td valign="top" style="padding: 5px 0; font-family: 'Poppins', sans-serif; font-size: 14px; font-weight: 700; color: #3b2412;">
                          October 9th, 2026
                        </td>
                      </tr>
                      <!-- Time -->
                      <tr>
                        <td width="90" valign="top" style="padding: 5px 0; font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 700; color: #9c7655; border-top: 1px dashed #e8d9cc;">
                          Time:
                        </td>
                        <td valign="top" style="padding: 5px 0; font-family: 'Poppins', sans-serif; font-size: 14px; font-weight: 700; color: #3b2412; border-top: 1px dashed #e8d9cc;">
                          10:00 AM &ndash; 4:20 PM
                        </td>
                      </tr>
                      <!-- Venue -->
                      <tr>
                        <td width="90" valign="top" style="padding: 5px 0; font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 700; color: #9c7655; border-top: 1px dashed #e8d9cc;">
                          Venue:
                        </td>
                        <td valign="top" style="padding: 5px 0; font-family: 'Poppins', sans-serif; font-size: 14px; font-weight: 800; color: #3b2412; border-top: 1px dashed #e8d9cc;">
                          Nalanda Auditorium, VBIT
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td bgcolor="#ffffff" style="background-color: #ffffff; padding: 8px 18px; border-top: 1.5px dashed #3b2412;">
                    <p style="margin: 0; font-family: 'Poppins', sans-serif; font-size: 12px; color: #6e4a2d; font-style: italic;">
                      &#9432; Further details will be communicated to you shortly.
                    </p>
                  </td>
                </tr>
              </table>

              <!-- WhatsApp Community Box -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f0fdf4; border-radius: 16px; border: 2px solid #86efac; box-shadow: 4px 4px 0px #86efac; margin-bottom: 22px; overflow: hidden;">
                <tr>
                  <td style="padding: 16px 18px;">
                    <p style="margin: 0 0 6px 0; font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 14px; font-weight: 800; color: #166534;">
                      &#128227; Join the Official Community for Updates
                    </p>
                    <p style="margin: 0; font-family: 'Poppins', sans-serif; font-size: 13px; line-height: 20px; color: #15803d;">
                      Please join the participant group immediately. All event schedules, live slot confirmations, reporting times, and venue announcements will be shared exclusively here:
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Action CTA Button (WhatsApp) -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px;">
                <tr>
                  <td align="center">
                    <a href="https://chat.whatsapp.com/DOvsMxujwYT8sN6Eyc5FKe" target="_blank" class="btn-wa" style="display: inline-block; background-color: #25D366; color: #ffffff; font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 15px; font-weight: 800; text-decoration: none; padding: 14px 30px; border-radius: 14px; border: 2px solid #3b2412; box-shadow: 4px 4px 0px #3b2412; letter-spacing: 0.03em; text-align: center;">
                      &#128172; Join Official WhatsApp Group &rarr;
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Direct link fallback -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 22px;">
                <tr>
                  <td style="background-color: #f8fafc; border-radius: 10px; border: 1px dashed #cbd5e1; padding: 10px 14px; text-align: center;">
                    <p style="margin: 0; font-family: 'Poppins', sans-serif; font-size: 11px; line-height: 16px; color: #64748b; word-break: break-all;">
                      Button not working? Copy &amp; paste this link: <a href="https://chat.whatsapp.com/DOvsMxujwYT8sN6Eyc5FKe" style="color: #16a34a; font-weight: 600; text-decoration: underline;">https://chat.whatsapp.com/DOvsMxujwYT8sN6Eyc5FKe</a>
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Instructions / Gate Guidelines -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 22px;">
                <tr>
                  <td style="background-color: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 14px 16px;">
                    <div style="font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 12px; font-weight: 800; color: #3b2412; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px;">
                      &#128204; Important Instructions for Event Day:
                    </div>
                    <ul style="margin: 0; padding-left: 18px; font-family: 'Poppins', sans-serif; font-size: 12px; line-height: 19px; color: #6e4a2d;">
                      <li style="margin-bottom: 4px;">Keep your <strong>Registration ID ({registration_id})</strong> or this email screenshot ready at the gate.</li>
                      <li style="margin-bottom: 4px;">All team members should report 15 minutes prior to the scheduled start (by <strong>9:45 AM</strong>).</li>
                      <li style="margin-bottom: 4px;">Bring your college ID cards for physical verification.</li>
                      <li>Carry your laptops, chargers, and any necessary tools for your chosen track.</li>
                    </ul>
                  </td>
                </tr>
              </table>

              <!-- Motivational Closing Message -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px;">
                <tr>
                  <td align="center" bgcolor="#fef08a" style="background-color: #fef08a; border-radius: 12px; border: 2px solid #3b2412; padding: 12px 18px; box-shadow: 3px 3px 0px #3b2412;">
                    <p style="margin: 0; font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 14px; font-weight: 800; color: #3b2412;">
                      &#128640; See you on the 9th &mdash; come ready to create, compete, and get things done!
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Divider Line -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 18px;">
                <tr>
                  <td style="border-top: 2px dashed #3b2412; font-size: 0; line-height: 0;">
                    &nbsp;
                  </td>
                </tr>
              </table>

              <!-- Sign-off & Branding -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <p style="margin: 0 0 4px 0; font-family: 'Quicksand', 'Poppins', sans-serif; font-size: 15px; font-weight: 800; color: #3b2412; letter-spacing: 0.06em; text-transform: uppercase;">
                      TEAM AARNA, VBIT
                    </p>
                    <p style="margin: 0; font-family: 'Poppins', sans-serif; font-size: 12px; color: #9c7655; font-weight: 500;">
                      Turning Passions into Profits &bull; Freelancing Club
                    </p>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Bottom Solid Accent Strip -->
          <tr>
            <td bgcolor="#3b2412" style="background-color: #3b2412; height: 6px; font-size: 0; line-height: 0;">
              &nbsp;
            </td>
          </tr>
        </table>
        <!--[if (gte mso 9)|(IE)]>
        </td>
        </tr>
        </table>
        <![endif]-->

        <!-- Email Footer -->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin-top: 18px;">
          <tr>
            <td align="center" style="font-family: 'Poppins', sans-serif; font-size: 11px; line-height: 16px; color: #9c7655;">
              <p style="margin: 0 0 4px 0;">
                You received this email because your team registered for <strong>Ishanya '26</strong> at AARNA, VBIT.
              </p>
              <p style="margin: 0;">
                &copy; 2026 AARNA Freelancing Club, VBIT. All rights reserved.
              </p>
            </td>
          </tr>
        </table>

      </td>
    </tr>
  </table>

</body>
</html>
"""


def send_status_email(to: str, team_name: str, registration_id: str, status: str, whatsapp_link: str = None):
    # Only send acceptance congratulations email; never send rejection / regret emails
    if status != "accepted":
        print(f"[EMAIL] Status is '{status}'. Skipping rejection/regret email to {to} as requested.")
        return None

    # Resolve official Ishanya WhatsApp group link
    official_whatsapp_link = whatsapp_link or getattr(settings, "ISHANYA_WHATSAPP_GROUP_LINK", None) or "https://chat.whatsapp.com/DOvsMxujwYT8sN6Eyc5FKe"
    if not official_whatsapp_link or official_whatsapp_link.strip() == "https://chat.whatsapp.com/":
        official_whatsapp_link = "https://chat.whatsapp.com/DOvsMxujwYT8sN6Eyc5FKe"

    adapter = get_email_adapter()
    subject = f"🎉 Registration Confirmed for ISHANYA'26! | Team {team_name} - Team AARNA"
    html_body = (
        ISHANYA_ACCEPTANCE_EMAIL_TEMPLATE
        .replace("{team_name}", str(team_name or "Participant"))
        .replace("{{team_name}}", str(team_name or "Participant"))
        .replace("{{TEAM_NAME}}", str(team_name or "Participant"))
        .replace("{registration_id}", str(registration_id or "N/A"))
        .replace("{{registration_id}}", str(registration_id or "N/A"))
        .replace("{{REGISTRATION_ID}}", str(registration_id or "N/A"))
        .replace("https://chat.whatsapp.com/DOvsMxujwYT8sN6Eyc5FKe", official_whatsapp_link)
        .replace("{whatsapp_link}", official_whatsapp_link)
        .replace("{{whatsapp_link}}", official_whatsapp_link)
        .replace("{{WHATSAPP_LINK}}", official_whatsapp_link)
    )

    return adapter.send(to, subject, html_body)
