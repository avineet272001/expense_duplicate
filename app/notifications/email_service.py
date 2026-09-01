import smtplib
import traceback
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.notifications.html_templates import (
    expense_approved_html
)
from email import encoders
from app.notifications.config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_EMAIL,
    SMTP_PASSWORD,
    SMTP_TLS
)

def send_email(to_email: str, subject: str, body: str):

    print("HOST :", SMTP_HOST)
    print("PORT :", SMTP_PORT)
    print("EMAIL:", SMTP_EMAIL)
    print("TLS  :", SMTP_TLS)

    try:
        print("Connecting...")

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20)

        print("Connected")

        server.set_debuglevel(1)

        server.ehlo()

        if SMTP_TLS:
            server.starttls()
            server.ehlo()

        print("Logging in...")

        server.login(SMTP_EMAIL, SMTP_PASSWORD)

        print("Logged in")

        message = MIMEMultipart()
        message["From"] = SMTP_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "html"))

        server.sendmail(
            SMTP_EMAIL,
            to_email,
            message.as_string()
        )

        print("Mail Sent")

        server.quit()

    except Exception:
        traceback.print_exc()



def send_email_with_attachment(
    to_email: str,
    subject: str,
    body: str,
    attachment: bytes,
    filename: str
 ):
    """
    Send an HTML email with a file attachment.

    Parameters
    ----------
    to_email:
        Email address of the recipient.

    subject:
        Email subject.

    body:
        HTML email body.

    attachment:
        File contents as bytes.
        For your report system this will be
        the generated PDF bytes.

    filename:
        Name shown to the recipient for the
        attached file.
    """

    try:
        print( "Connecting to SMTP server...")
        server = smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=20
        )

        print("Connected to SMTP server")
        server.ehlo()
        # ----------------------------------------------------
        # START TLS
        # ----------------------------------------------------

        if SMTP_TLS:
            server.starttls()
            server.ehlo()

        # ---------------------------------------
        # LOGIN
        # ---------------------------------------

        print("Logging in to SMTP server...")

        server.login(
            SMTP_EMAIL,
            SMTP_PASSWORD
        )

        print("SMTP login successful")   

        #-----------------
        # CREATE EMAIL
        # ---------------

        message = MIMEMultipart()

        message["From"] = SMTP_EMAIL
        message["TO"] = to_email
        message["SUBJECT"] = subject
        # ----------------------------------------------------
        # HTML BODY
        # ----------------------------------------------------


        message.attach(
            MIMEText(
                body,
                "html"
            )
        )

        # ------ 
        # PDF CONNECTION 
        # ------

        pdf_part = MIMEBase(
            "application",
            "pdf"
        )

        pdf_part.set_payload(
            attachment
        )

        encoders.encode_base64(
            pdf_part
        )

        pdf_part.add_header(
            "Content-Disposition",
            f'attachment; filename="{filename}"'
        )

        message.attach(
            pdf_part
        )


        server.sendmail(
            SMTP_EMAIL,
            to_email,
            message.as_string()
        )

        print(
            f"Email with attachment sent successfully "
            f"to {to_email}"
        )

        print(
            f"Attachment: {filename}"
        )

        server.quit()

    except Exception:
        print(
            "Failed to send email with attachment"
        )

        traceback.print_exc()

        raise




 
    
