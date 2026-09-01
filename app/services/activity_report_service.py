import os

from datetime import datetime, timedelta

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors

from app.database import SessionLocal
from app.models import SubVendorActivityLog

from app.services.email_service import (
    send_activity_email_safe
)


REPORT_DIRECTORY = "reports"


def generate_daily_sub_vendor_activity_report():

    db = SessionLocal()

    try:



        today = datetime.now().date()

        start_datetime = datetime.combine(
            today,
            datetime.min.time()
        )

        end_datetime = start_datetime + timedelta(
            days=1
        )



        activities = (
            db.query(SubVendorActivityLog)
            .filter(
                SubVendorActivityLog.created_at
                >= start_datetime,

                SubVendorActivityLog.created_at
                < end_datetime
            )
            .order_by(
                SubVendorActivityLog.created_at.asc()
            )
            .all()
        )

 

        os.makedirs(
            REPORT_DIRECTORY,
            exist_ok=True
        )

        pdf_filename = (
            f"daily_sub_vendor_activity_report_"
            f"{today}.pdf"
        )

        pdf_path = os.path.join(
            REPORT_DIRECTORY,
            pdf_filename
        )



        document = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        styles = getSampleStyleSheet()

        title_style = styles["Title"]
        title_style.alignment = TA_CENTER

        heading_style = styles["Heading2"]
        normal_style = styles["BodyText"]

        elements = []

        elements.append(
            Paragraph(
                "Daily Sub-Vendor Activity Report",
                title_style
            )
        )

        elements.append(
            Spacer(1, 10)
        )

        elements.append(
            Paragraph(
                f"Report Date: {today}",
                normal_style
            )
        )

        elements.append(
            Spacer(1, 15)
        )



        if not activities:

            elements.append(
                Paragraph(
                    "No sub-vendor activity was recorded today.",
                    normal_style
                )
            )

        else:

            elements.append(
                Paragraph(
                    f"Total Activities: {len(activities)}",
                    heading_style
                )
            )

            elements.append(
                Spacer(1, 10)
            )


            table_data = [
                [
                    "ID",
                    "User",
                    "Action",
                    "Module",
                    "Record",
                    "Status",
                    "Created At"
                ]
            ]

            for activity in activities:

                created_at = ""

                if activity.created_at:

                    created_at = (
                        activity.created_at
                        .strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )

                table_data.append(
                    [
                        str(activity.id),
                        str(activity.user_id),
                        activity.action or "",
                        activity.module or "",
                        (
                            str(activity.record_id)
                            if activity.record_id
                            else ""
                        ),
                        activity.status or "",
                        created_at
                    ]
                )

         

            table = Table(
                table_data,
                repeatRows=1,
                colWidths=[
                    30,
                    40,
                    85,
                    65,
                    45,
                    55,
                    100
                ]
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.lightgrey
                        ),

                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            colors.black
                        ),

                        (
                            "FONTNAME",
                            (0, 0),
                            (-1, 0),
                            "Helvetica-Bold"
                        ),

                        (
                            "FONTSIZE",
                            (0, 0),
                            (-1, -1),
                            7
                        ),

                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.grey
                        ),

                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP"
                        ),

                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            4
                        ),

                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            4
                        ),

                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            5
                        ),

                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            5
                        ),
                    ]
                )
            )

            elements.append(table)

            elements.append(
                Spacer(1, 15)
            )


            elements.append(
                Paragraph(
                    "Activity Details",
                    heading_style
                )
            )

            elements.append(
                Spacer(1, 10)
            )

            for activity in activities:

                description = (
                    activity.description
                    or "No description"
                )

                details = (
                    activity.details
                    or ""
                )

                text = (
                    f"<b>Activity ID:</b> "
                    f"{activity.id}<br/>"
                    f"<b>Action:</b> "
                    f"{activity.action}<br/>"
                    f"<b>Module:</b> "
                    f"{activity.module}<br/>"
                    f"<b>User ID:</b> "
                    f"{activity.user_id}<br/>"
                    f"<b>Record ID:</b> "
                    f"{activity.record_id}<br/>"
                    f"<b>Status:</b> "
                    f"{activity.status}<br/>"
                    f"<b>Description:</b> "
                    f"{description}<br/>"
                )

                if details:

                    text += (
                        f"<b>Details:</b> "
                        f"{details}<br/>"
                    )

                if activity.created_at:

                    text += (
                        f"<b>Created At:</b> "
                        f"{activity.created_at}"
                    )

                elements.append(
                    Paragraph(
                        text,
                        normal_style
                    )
                )

                elements.append(
                    Spacer(1, 10)
                )



        document.build(elements)

        print(
            f"PDF report created: {pdf_path}"
        )


        email_sent = send_activity_email_safe(
            subject=(
                f"Daily Sub-Vendor Activity Report - "
                f"{today}"
            ),

            body=(
                f"Hello,\n\n"
                f"Please find attached the Daily "
                f"Sub-Vendor Activity Report "
                f"for {today}.\n\n"
                f"Total activities: "
                f"{len(activities)}\n\n"
                f"Regards,\n"
                f"Expense Management System"
            ),

            attachment_path=pdf_path
        )

        return email_sent

    finally:

        db.close()