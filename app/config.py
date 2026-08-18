import os
from urllib.parse import quote_plus
from dotenv import load_dotenv


load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
    raise Exception("One or more database environment variables are missing.")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print(DATABASE_URL)  


ADMIN_REPORT_EMAIL = os.getenv(
    "ADMIN_REPORT_EMAIL"
)


# ============================================================
# ADMIN USER ID (used to route Firebase push notifications
# raised by sub-vendor actions to the admin dashboard)
# ============================================================

ADMIN_USER_ID = int(
    os.getenv("ADMIN_USER_ID", "1")
)



# For the Report  Genearation 

DAILY_REPORT_HOUR = int(
    os.getenv("DAILY_REPORT_HOUR", "10")
)

DAILY_REPORT_MINUTE = int(
    os.getenv("DAILY_REPORT_MINUTE", "0")
)

WEEKLY_REPORT_DAY = os.getenv(
    "WEEKLY_REPORT_DAY",
    "mon"
)

WEEKLY_REPORT_HOUR = int(
    os.getenv("WEEKLY_REPORT_HOUR", "8")
)

WEEKLY_REPORT_MINUTE = int(
    os.getenv("WEEKLY_REPORT_MINUTE", "0")
)

MONTHLY_REPORT_DAY = int(
    os.getenv("MONTHLY_REPORT_DAY", "1")
)

MONTHLY_REPORT_HOUR = int(
    os.getenv("MONTHLY_REPORT_HOUR", "8")
)

MONTHLY_REPORT_MINUTE = int(
    os.getenv("MONTHLY_REPORT_MINUTE", "0")
)



