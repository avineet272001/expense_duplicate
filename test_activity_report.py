from app.services.activity_report_service import (
    generate_daily_sub_vendor_activity_report
)


result = generate_daily_sub_vendor_activity_report()

print(
    "REPORT RESULT:",
    result
)