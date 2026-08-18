from io import BytesIO
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_category_subcategory_report_pdf(
    report_rows,
    start_date,
    end_date,
):
    """
    Generate Category and Subcategory report PDF.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            "Category and Subcategory Report",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            f"<b>From:</b> {start_date}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>To:</b> {end_date}",
            styles["Normal"]
        )
    )

    story.append(
        Spacer(1, 15)
    )

    # ========================================================
    # TABLE HEADER
    # ========================================================

    table_data = [
        [
            "Category",
            "Subcategory",
            "Expense Count",
            "Total Amount",
        ]
    ]

    # ========================================================
    # TOTAL VARIABLES
    # ========================================================

    total_count = 0
    total_amount = Decimal("0")

    # ========================================================
    # CATEGORY/SUBCATEGORY ROWS
    # ========================================================

    for row in report_rows:

        count = int(
            row["expense_count"]
        )

        amount = Decimal(
            str(row["total_amount"])
        )

        # -----------------------------------------------
        # Add to overall totals
        # -----------------------------------------------

        total_count += count
        total_amount += amount

        # -----------------------------------------------
        # Add category/subcategory row
        # -----------------------------------------------

        table_data.append(
            [
                row["category_name"],
                row["subcategory_name"],
                str(count),
                f"₹ {amount:,.2f}",
            ]
        )

    # ========================================================
    # TOTAL ROW
    #
    # IMPORTANT:
    # This is OUTSIDE the for loop.
    # ========================================================

    table_data.append(
        [
            "TOTAL",
            "",
            str(total_count),
            f"₹ {total_amount:,.2f}",
        ]
    )

    # ========================================================
    # TABLE
    # ========================================================

    table = Table(
        table_data,
        colWidths=[
            60 * mm,
            60 * mm,
            35 * mm,
            40 * mm,
        ]
    )

    # ========================================================
    # TABLE STYLE
    # ========================================================

    table.setStyle(
        TableStyle(
            [

                # --------------------------------------------
                # Header
                # --------------------------------------------

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f2937"),
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),

                # --------------------------------------------
                # Alignment
                # --------------------------------------------

                (
                    "ALIGN",
                    (2, 1),
                    (-1, -1),
                    "RIGHT",
                ),

                # --------------------------------------------
                # Borders
                # --------------------------------------------

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),

                # --------------------------------------------
                # TOTAL ROW
                # --------------------------------------------

                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold",
                ),

                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.lightgrey,
                ),

                # --------------------------------------------
                # Vertical alignment
                # --------------------------------------------

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                # --------------------------------------------
                # Padding
                # --------------------------------------------

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    # ========================================================
    # ADD TABLE TO PDF
    # ========================================================

    story.append(table)

    story.append(
        Spacer(1, 20)
    )

    # ========================================================
    # FOOTER
    # ========================================================

    story.append(
        Paragraph(
            "Generated by Expense Management System",
            styles["Normal"]
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(story)

    buffer.seek(0)

    return buffer
