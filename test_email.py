# import os
# import smtplib

# from dotenv import load_dotenv

# load_dotenv()

# SMTP_HOST = os.getenv("SMTP_HOST")
# SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
# SMTP_EMAIL = os.getenv("SMTP_EMAIL")
# SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
# ADMIN_EMAIL = os.getenv("ADMIN_REPORT_EMAIL")

# print("HOST:", SMTP_HOST)
# print("PORT:", SMTP_PORT)
# print("FROM:", SMTP_EMAIL)
# print("TO:", ADMIN_EMAIL)
# print("PASSWORD SET:", bool(SMTP_PASSWORD))

# try:

#     print("\nConnecting to Gmail...")

#     server = smtplib.SMTP(
#         SMTP_HOST,
#         SMTP_PORT,
#         timeout=20
#     )

#     print("SMTP connection successful")

#     server.ehlo()

#     print("Starting TLS...")

#     server.starttls()

#     print("TLS successful")

#     server.ehlo()

#     print("Logging in...")

#     server.login(
#         SMTP_EMAIL,
#         SMTP_PASSWORD
#     )

#     print("SMTP login successful")

#     message = f"""\
# From: {SMTP_EMAIL}
# To: {ADMIN_EMAIL}
# Subject: Expense Management Test

# This is a test email from the Expense Management backend.
# """

#     print("Sending email...")

#     server.sendmail(
#         SMTP_EMAIL,
#         ADMIN_EMAIL,
#         message
#     )

#     print("EMAIL SENT SUCCESSFULLY")

#     server.quit()

# except Exception as e:

#     print("\nEMAIL TEST FAILED")
#     print("ERROR TYPE:", type(e).__name__)
#     print("ERROR:", str(e))




from app.services.email_service import send_activity_email_safe


result = send_activity_email_safe(
    subject="Activity Service Test",
    body="""
Sub-Vendor Activity Test

This email was sent through
app.services.email_service.
"""
)

print("RESULT:", result)