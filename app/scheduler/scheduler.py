from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import (
    BackgroundScheduler
)
from app.services.activity_report_service import (
    generate_daily_sub_vendor_activity_report
)
from app.scheduler.jobs import (
    daily_payment_report_job,
    monthly_payment_report_job,
    daily_sub_vendor_activity_report_job,
    monthly_category_subcategory_report_job,
)

from app.config import (
    DAILY_REPORT_HOUR,
    DAILY_REPORT_MINUTE,
    MONTHLY_REPORT_DAY,
    MONTHLY_REPORT_HOUR,
    MONTHLY_REPORT_MINUTE,
)


# ============================================================
# SCHEDULER
# ============================================================

scheduler = BackgroundScheduler(
    timezone=ZoneInfo("Asia/Kolkata")
)


# ============================================================
# START SCHEDULER
# ============================================================

def start_scheduler():

    # --------------------------------------------------------
    # PREVENT STARTING THE SAME SCHEDULER TWICE
    # --------------------------------------------------------

    if scheduler.running:

        print(
            "Report scheduler is already running."
        )

        return

    # ========================================================
    # DAILY REPORT
    # ========================================================

    scheduler.add_job(
        daily_payment_report_job,

        trigger="cron",

        hour=DAILY_REPORT_HOUR,
        minute=DAILY_REPORT_MINUTE,

        id="daily_payment_report",

        replace_existing=True,
    )

    # ========================================================
    # MONTHLY REPORT
    # ========================================================

    scheduler.add_job(
        monthly_payment_report_job,

        trigger="cron",

        day=MONTHLY_REPORT_DAY,

        hour=MONTHLY_REPORT_HOUR,
        minute=MONTHLY_REPORT_MINUTE,

        id="monthly_payment_report",

        replace_existing=True,
    )

    # ========================================================
    # START
    # ========================================================

    scheduler.start()

    print(
        "========================================"
    )

    print(
        "REPORT SCHEDULER STARTED"
    )

    print(
        f"Daily report scheduled at "
        f"{DAILY_REPORT_HOUR:02d}:"
        f"{DAILY_REPORT_MINUTE:02d}"
    )

    print(
        f"Monthly report scheduled on day "
        f"{MONTHLY_REPORT_DAY} at "
        f"{MONTHLY_REPORT_HOUR:02d}:"
        f"{MONTHLY_REPORT_MINUTE:02d}"
    )

    print(
        "========================================"
    )


    # ========================================================
    #    DAILY SUB-VENDOR ACTIVITY REPORT
    # ========================================================

    scheduler.add_job(
    daily_sub_vendor_activity_report_job,
    trigger="cron",
    hour=DAILY_REPORT_HOUR,
    minute=DAILY_REPORT_MINUTE,
    id="daily_sub_vendor_activity_report",
    replace_existing=True,
    )

def daily_sub_vendor_activity_report_job():

    print(
        "Starting daily sub-vendor activity report..."
    )

    try:

        result = (
            generate_daily_sub_vendor_activity_report()
        )

        if result:

            print(
                "Daily sub-vendor activity report "
                "sent successfully."
            )

        else:

            print(
                "Daily sub-vendor activity report "
                "failed to send."
            )

    except Exception as e:

        print(
            "Daily sub-vendor activity report "
            f"failed: {e}"
        )


scheduler.add_job(
    monthly_category_subcategory_report_job,

    trigger="cron",

    day=MONTHLY_REPORT_DAY,
    hour=MONTHLY_REPORT_HOUR,
    minute=MONTHLY_REPORT_MINUTE,

    id="monthly_category_subcategory_report",

    replace_existing=True,
)