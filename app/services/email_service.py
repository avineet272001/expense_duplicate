import os
import smtplib

from dotenv import load_dotenv

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

SMTP_USERNAME = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

ADMIN_EMAIL = os.getenv("ADMIN_REPORT_EMAIL")


def send_activity_email(
    subject: str,
    body: str,
    attachment_path: str | None = None
):

    message = MIMEMultipart()

    message["From"] = SMTP_USERNAME
    message["To"] = ADMIN_EMAIL
    message["Subject"] = subject

    # Email body
    message.attach(
        MIMEText(body, "plain")
    )



    if attachment_path:

        with open(
            attachment_path,
            "rb"
        ) as file:

            pdf_attachment = MIMEApplication(
                file.read(),
                _subtype="pdf"
            )

        filename = os.path.basename(
            attachment_path
        )

        pdf_attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=filename
        )

        message.attach(
            pdf_attachment
        )



    server = smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
        timeout=20
    )

    try:

        server.ehlo()

        server.starttls()

        server.ehlo()

        server.login(
            SMTP_USERNAME,
            SMTP_PASSWORD
        )

        server.sendmail(
            SMTP_USERNAME,
            ADMIN_EMAIL,
            message.as_string()
        )

    finally:

        server.quit()


def send_activity_email_safe(
    subject: str,
    body: str,
    attachment_path: str | None = None
):

    try:

        send_activity_email(
            subject=subject,
            body=body,
            attachment_path=attachment_path
        )

        print(
            "Activity email sent successfully"
        )

        return True

    except Exception as e:

        print(
            f"Activity email failed: {e}"
        )

        return False