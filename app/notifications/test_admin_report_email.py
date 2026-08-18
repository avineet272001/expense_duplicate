from datetime import date

from app.notifications.email_service import (
    send_email_with_attachment
)

from app.notifications.config import (
    ADMIN_REPORT_EMAIL
)

from app.services.payment_report_pdf import (
    generate_payment_report_pdf
)


def test_admin_payment_report_email():

    # ========================================================
    # TEST DATA
    # ========================================================

    report_rows = [
        {
            "payment_method_name": "Cash",
            "payment_count": 2,
            "total_amount": 5000,
        },
        {
            "payment_method_name": "UPI",
            "payment_count": 4,
            "total_amount": 12000,
        },
        {
            "payment_method_name": "Cheque",
            "payment_count": 3,
            "total_amount": 18000,
        },
    ]

    start_date = date(
        2026,
        8,
        1
    )

    end_date = date(
        2026,
        8,
        12
    )

    # ========================================================
    # GENERATE PDF
    # ========================================================

    pdf_buffer = generate_payment_report_pdf(
        report_rows=report_rows,
        period="custom",
        start_date=start_date,
        end_date=end_date,
    )

    # ========================================================
    # CONVERT PDF TO BYTES
    # ========================================================

    pdf_bytes = pdf_buffer.getvalue()

    print(
        "PDF generated:",
        len(pdf_bytes),
        "bytes"
    )

    # ========================================================
    # SEND PDF TO ADMIN
    # ========================================================

    send_email_with_attachment(

        to_email=ADMIN_REPORT_EMAIL,

        subject="Test Payment Report",

        body=f"""
        <html>
            <body>

                <h2>
                    Expense Management System
                </h2>

                <p>
                    This is a test payment report.
                </p>

                <p>
                    Report Period:
                    <b>{start_date}</b>
                    to
                    <b>{end_date}</b>
                </p>

                <p>
                    Please find the PDF report
                    attached to this email.
                </p>

                <p>
                    Regards,<br>
                    Expense Management System
                </p>

            </body>
        </html>
        """,

        attachment=pdf_bytes,

        filename=(
            f"payment_report_"
            f"{start_date}_"
            f"{end_date}.pdf"
        )
    )


# ============================================================
# RUN TEST
# ============================================================

if __name__ == "__main__":

    test_admin_payment_report_email()