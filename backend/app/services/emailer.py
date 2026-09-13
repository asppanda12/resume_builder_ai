"""Email the rendered resume PDF through Gmail SMTP (smtp.gmail.com:465, SSL) with an App Password.

To switch to the Gmail API with OAuth2 instead of an App Password:
  1. In Google Cloud Console enable the Gmail API and create an OAuth client (Desktop app).
  2. pip install google-api-python-client google-auth-oauthlib
  3. Get user credentials once with scope "https://www.googleapis.com/auth/gmail.send", e.g.
       creds = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES).run_local_server()
     then store creds.to_json() and reload it with Credentials.from_authorized_user_info(...).
  4. Replace _send_via_smtp() with:
       service = googleapiclient.discovery.build("gmail", "v1", credentials=creds)
       raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
       service.users().messages().send(userId="me", body={"raw": raw}).execute()
The EmailMessage built by _build_message() works unchanged with both transports.
"""
import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from app.config import get_settings
from app.errors import AppError

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

EMAIL_BODY = """Hi,

Attached is the latest version of your resume, generated with AI Resume Builder.

Good luck with your application!
"""


def _build_message(*, sender: str, to: str, candidate_name: str, pdf: bytes, filename: str) -> EmailMessage:
    name = " ".join(candidate_name.split())  # also strips newlines, so the name can't inject headers
    message = EmailMessage()
    message["Subject"] = f"Resume: {name}" if name else "Your resume"
    message["From"] = sender
    message["To"] = to
    message.set_content(EMAIL_BODY)
    message.add_attachment(pdf, maintype="application", subtype="pdf", filename=filename)
    return message


def _send_via_smtp(message: EmailMessage, address: str, app_password: str) -> None:
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ssl.create_default_context(), timeout=30) as smtp:
        smtp.login(address, app_password)
        smtp.send_message(message)


async def send_resume(*, to: str | None, candidate_name: str, pdf: bytes, filename: str) -> str:
    settings = get_settings()
    if not (settings.gmail_address and settings.gmail_app_password):
        raise AppError(
            "Email isn't configured. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env.",
            status_code=503,
            code="email_not_configured",
        )
    recipient = to or settings.gmail_address
    message = _build_message(
        sender=settings.gmail_address, to=recipient, candidate_name=candidate_name, pdf=pdf, filename=filename
    )
    # Google displays App Passwords as "abcd efgh ijkl mnop"; the spaces aren't part of it.
    app_password = settings.gmail_app_password.replace(" ", "")
    try:
        await asyncio.to_thread(_send_via_smtp, message, settings.gmail_address, app_password)
    except smtplib.SMTPAuthenticationError as exc:
        raise AppError(
            "Gmail rejected the login. GMAIL_APP_PASSWORD must be a 16-character App Password, not your account password.",
            status_code=502,
            code="email_auth_failed",
        ) from exc
    except (smtplib.SMTPException, OSError) as exc:
        raise AppError(f"Sending the email failed: {exc}", status_code=502, code="email_failed") from exc
    return recipient
