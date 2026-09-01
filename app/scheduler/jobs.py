from datetime import date, timedelta

from app.database import SessionLocal
from app.services.activity_report_service import (
    generate_daily_sub_vendor_activity_report
)
from app.crud import (
    get_category_subcategory_period_report,
    get_payment_period_report,
)

from app.services.payment_report_pdf import (
    generate_payment_report_pdf,
)
from app.services.category_subcategory_report_pdf import (
    generate_category_subcategory_report_pdf,
)

from app.notifications.email_service import (
    send_email_with_attachment,
)

from app.notifications.config import (
    ADMIN_REPORT_EMAIL,
)


def get_previous_month_range():
    """Return the first and last day of the previous month."""
    today = date.today()
    first_day_current_month = today.replace(day=1)
    end_date = first_day_current_month - timedelta(days=1)
    start_date = end_date.replace(day=1)
    return start_date, end_date


def daily_payment_report_job():

    print("\n========================================")
    print("DAILY PAYMENT REPORT JOB STARTED")
    print("========================================")

    db = SessionLocal()

    try:



        report_date = date.today()

        start_date = report_date
        end_date = report_date

        print(
            f"Generating daily report "
            f"for {start_date}"
        )



        report_rows = get_payment_period_report(
            db=db,
            start_date=start_date,
            end_date=end_date
        )

        print(
            f"Report rows found: "
            f"{len(report_rows)}"
        )



        for row in report_rows:

            print(
                f"Payment Method: "
                f"{row['payment_method_name']} | "
                f"Count: {row['payment_count']} | "
                f"Amount: {row['total_amount']}"
            )



        pdf_buffer = generate_payment_report_pdf(
            report_rows=report_rows,
            period="daily",
            start_date=start_date,
            end_date=end_date
        )



        pdf_bytes = pdf_buffer.getvalue()

        print(
            f"PDF generated successfully"
        )

        print(
            f"PDF size: {len(pdf_bytes)} bytes"
        )


        filename = (
            f"daily_payment_report_"
            f"{start_date}.pdf"
        )

   

        send_email_with_attachment(

            to_email=ADMIN_REPORT_EMAIL,

            subject=(
                f"Daily Payment Report - "
                f"{start_date}"
            ),

            body=f"""
            <html>
                <body>

                    <h2>
                        Daily Payment Report
                    </h2>

                    <p>
                        Please find the daily
                        payment report attached.
                    </p>

                    <p>
                        <b>Report Date:</b>
                        {start_date}
                    </p>

                    <p>
                        This report was
                        automatically generated
                        by the Expense Management
                        System.
                    </p>

                    <p>
                        Regards,<br>
                        Expense Management System
                    </p>

                </body>
            </html>
            """,

            attachment=pdf_bytes,

            filename=filename
        )

        print(
            "Daily report email sent successfully"
        )

        print(
            "========================================"
        )

        print(
            "DAILY PAYMENT REPORT JOB COMPLETED"
        )

        print(
            "========================================"
        )

    except Exception as e:

        print(
            "\n========================================"
        )

        print(
            "DAILY PAYMENT REPORT JOB FAILED"
        )

        print(
            "========================================"
        )

        print(
            f"Error: {e}"
        )

        raise

    finally:

        db.close()


def monthly_payment_report_job():

    print("\n========================================")
    print("MONTHLY PAYMENT REPORT JOB STARTED")
    print("========================================")

    db = SessionLocal()

    try:



        today = date.today()

        print(
            f"Current date: {today}"
        )



        first_day_current_month = today.replace(
            day=1
        )



        end_date = (
            first_day_current_month
            - timedelta(days=1)
        )


        start_date = end_date.replace(
            day=1
        )

        print(
            f"Monthly report range: "
            f"{start_date} → {end_date}"
        )



        report_rows = get_payment_period_report(
            db=db,
            start_date=start_date,
            end_date=end_date
        )

        print(
            f"Report rows found: "
            f"{len(report_rows)}"
        )


        for row in report_rows:

            print(
                f"Payment Method: "
                f"{row['payment_method_name']} | "
                f"Count: {row['payment_count']} | "
                f"Amount: {row['total_amount']}"
            )



        pdf_buffer = generate_payment_report_pdf(
            report_rows=report_rows,
            period="monthly",
            start_date=start_date,
            end_date=end_date
        )

        pdf_bytes = pdf_buffer.getvalue()

        print(
            f"PDF generated successfully"
        )

        print(
            f"PDF size: {len(pdf_bytes)} bytes"
        )

        filename = (
            f"monthly_payment_report_"
            f"{start_date.strftime('%Y_%m')}.pdf"
        )



        send_email_with_attachment(

            to_email=ADMIN_REPORT_EMAIL,

            subject=(
                f"Monthly Payment Report - "
                f"{start_date.strftime('%B %Y')}"
            ),

            body=f"""
            <html>
                <body>

                    <h2>
                        Monthly Payment Report
                    </h2>

                    <p>
                        Please find the monthly
                        payment report attached.
                    </p>

                    <p>
                        <b>Report Period:</b>
                        {start_date}
                        to
                        {end_date}
                    </p>

                    <p>
                        This report was automatically
                        generated by the Expense
                        Management System.
                    </p>

                    <p>
                        Regards,<br>
                        Expense Management System
                    </p>

                </body>
            </html>
            """,

            attachment=pdf_bytes,

            filename=filename
        )

        print(
            "Monthly report email sent successfully"
        )

        print("\n========================================")
        print("MONTHLY PAYMENT REPORT JOB COMPLETED")
        print("========================================\n")

    except Exception as e:

        print(
            "\n========================================"
        )

        print(
            "MONTHLY PAYMENT REPORT JOB FAILED"
        )

        print(
            "========================================"
        )

        print(
            f"Error: {e}"
        )

        raise

    finally:

        db.close()  


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
                "Daily sub-vendor activity PDF "
                "sent successfully."
            )

        else:

            print(
                "Daily sub-vendor activity PDF "
                "failed to send."
            )

    except Exception as e:

        print(
            "Daily sub-vendor activity report "
            f"failed: {e}"
        )              



def monthly_category_subcategory_report_job():

    print(
        "\n========================================"
    )

    print(
        "MONTHLY CATEGORY + SUBCATEGORY REPORT"
    )

    print(
        "========================================"
    )

    db = SessionLocal()

    try:



        start_date, end_date = (
            get_previous_month_range()
        )

        print(
            f"Report period: "
            f"{start_date} to {end_date}"
        )


        report_rows = (
            get_category_subcategory_period_report(
                db=db,
                start_date=start_date,
                end_date=end_date
            )
        )

        print(
            f"Report rows: {len(report_rows)}"
        )



        pdf_buffer = (
            generate_category_subcategory_report_pdf(
                report_rows=report_rows,
                start_date=start_date,
                end_date=end_date
            )
        )

        pdf_bytes = pdf_buffer.getvalue()



        month_name = start_date.strftime("%B_%Y")

        filename = (
            f"category_subcategory_report_"
            f"{month_name}.pdf"
        )

        send_email_with_attachment(

            to_email=ADMIN_REPORT_EMAIL,

            subject=(
                "Monthly Category & Subcategory "
                f"Expense Report - "
                f"{start_date.strftime('%B %Y')}"
            ),

            body=f"""
            <html>
                <body>

                    <h2>
                        Monthly Expense Report
                    </h2>

                    <p>
                        Please find the monthly
                        Category & Subcategory
                        expense report attached.
                    </p>

                    <p>
                        <b>Report Period:</b>
                        {start_date}
                        to
                        {end_date}
                    </p>

                    <p>
                        The PDF contains:
                    </p>

                    <ul>
                        <li>Category-wise expenses</li>
                        <li>Subcategory-wise expenses</li>
                        <li>Expense count</li>
                        <li>Total amount</li>
                    </ul>

                    <p>
                        This report was automatically
                        generated by the Expense
                        Management System.
                    </p>

                </body>
            </html>
            """,

            attachment=pdf_bytes,

            filename=filename
        )

        print(
            "Monthly category/subcategory "
            "report email sent successfully."
        )

    except Exception as e:

        print(
            "Monthly category/subcategory "
            f"report failed: {e}"
        )

        raise

    finally:

        db.close()        \











def test_august_category_subcategory_report():

    db = SessionLocal()

    try:
        start_date = date(2026, 8, 1)
        end_date = date(2026, 8, 31)

        print(
            f"Testing report for "
            f"{start_date} to {end_date}"
        )

        report_rows = (
            get_category_subcategory_period_report(
                db=db,
                start_date=start_date,
                end_date=end_date,
            )
        )

        print(
            f"Real August records found: "
            f"{len(report_rows)}"
        )

        for row in report_rows:
            print(
                row["category_name"],
                "|",
                row["subcategory_name"],
                "|",
                row["expense_count"],
                "|",
                row["total_amount"],
            )

        pdf_buffer = (
            generate_category_subcategory_report_pdf(
                report_rows=report_rows,
                start_date=start_date,
                end_date=end_date,
            )
        )

        pdf_bytes = pdf_buffer.getvalue()

        filename = (
            "category_subcategory_report_August_2026.pdf"
        )

        send_email_with_attachment(
            to_email=ADMIN_REPORT_EMAIL,
            subject=(
                "TEST - Category & Subcategory "
                "Expense Report - August 2026"
            ),
            body="""
            <html>
                <body>
                    <h2>August 2026 Expense Report</h2>

                    <p>
                        This is a test report generated
                        using the real expense data from
                        the database.
                    </p>

                    <p>
                        Report Period:
                        01-Aug-2026 to 31-Aug-2026
                    </p>

                    <p>
                        The attached PDF contains the
                        category and subcategory report.
                    </p>
                </body>
            </html>
            """,
            attachment=pdf_bytes,
            filename=filename,
        )

        print(
            "August report email sent successfully."
        )

    except Exception as e:

        print(
            f"August report failed: {e}"
        )

        raise

    finally:
        db.close()        