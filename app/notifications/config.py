import os
from dotenv import load_dotenv
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

SMTP_TLS = os.getenv("SMTP_TLS") == "True"

ADMIN_REPORT_EMAIL = os.getenv(
    "ADMIN_REPORT_EMAIL"
)