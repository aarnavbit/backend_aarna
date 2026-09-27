import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


class EmailAdapter:
    def send(self, to: str, subject: str, html_body: str):
        raise NotImplementedError


class SMTPAdapter(EmailAdapter):
    def send(self, to: str, subject: str, html_body: str):
        if not settings.ISHANYA_SMTP_USER or not settings.ISHANYA_SMTP_PASS:
            print(f"[EMAIL] SMTP not configured, skipping email to {to}: {subject}")
            return

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.ISHANYA_EMAIL_FROM
            msg["To"] = to
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.ISHANYA_SMTP_HOST, settings.ISHANYA_SMTP_PORT) as server:
                server.starttls()
                server.login(settings.ISHANYA_SMTP_USER, settings.ISHANYA_SMTP_PASS)
                server.sendmail(settings.ISHANYA_EMAIL_FROM, to, msg.as_string())

            print(f"[EMAIL] Sent to {to}: {subject}")
        except Exception as e:
            print(f"[EMAIL] Failed to send to {to}: {e}")


_adapter = SMTPAdapter()


def send_status_email(to: str, team_name: str, registration_id: str, status: str, whatsapp_link: str):
    if status == "accepted":
        subject = f"Congratulations! Team {team_name} has been accepted - Ishanya"
        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
            <h2 style="color:#16a34a;">🎉 Congratulations!</h2>
            <p>Your team <strong>{team_name}</strong> (ID: <code>{registration_id}</code>) has been <strong style="color:#16a34a;">accepted</strong> for Ishanya!</p>
            <p>Please join our WhatsApp group for further updates:</p>
            <a href="{whatsapp_link}" style="display:inline-block;background:#25D366;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;margin:16px 0;">
                Join WhatsApp Group
            </a>
            <p style="color:#666;font-size:0.85em;margin-top:24px;">— Team Aarna</p>
        </div>
        """
    else:
        subject = f"Ishanya Registration Update — Team {team_name}"
        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
            <h2 style="color:#dc2626;">Registration Update</h2>
            <p>We regret to inform you that your team <strong>{team_name}</strong> (ID: <code>{registration_id}</code>) could not be accepted for Ishanya at this time.</p>
            <p>If you have any questions, please contact us at our official channels.</p>
            <p style="color:#666;font-size:0.85em;margin-top:24px;">— Team Aarna</p>
        </div>
        """

    _adapter.send(to, subject, html_body)
