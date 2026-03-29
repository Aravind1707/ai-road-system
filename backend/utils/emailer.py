import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL, AUTHORITY_EMAIL


def send_authority_report(subject: str, body: str, to_email: str = AUTHORITY_EMAIL):
    message = MIMEMultipart()
    message["From"] = FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, message.as_string())
        server.quit()
        return True
    except Exception as exc:
        print("Email report failed:", exc)
        return False
