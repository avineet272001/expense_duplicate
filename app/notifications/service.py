from app.notifications.email_service import send_email


from app.notifications.html_templates import expense_approved_html
from app.notifications.templates import (
    expense_created_template,
    expense_approved_template,
    expense_rejected_template,
    expense_paid_template
)


def send_expense_created_email(
    email,
    employee_name,
    expense_id,
    amount
):

    subject, body = expense_created_template(
        employee_name,
        expense_id,
        amount
    )

    send_email(
        email,
        subject,
        body
    )


def send_expense_approved_email(
    email,
    employee_name,
    expense_id,
    amount
):

    subject, body = expense_approved_html(
        employee_name,
        expense_id,
        amount
    )

    send_email(
        email,
        subject,
        body
    )


def send_expense_rejected_email(
    email,
    employee_name,
    expense_id,
    remarks
):

    subject, body = expense_rejected_template(
        employee_name,
        expense_id,
        remarks
    )

    send_email(
        email,
        subject,
        body
    )


def send_expense_paid_email(
    email,
    employee_name,
    expense_id,
    amount
):

    subject, body = expense_paid_template(
        employee_name,
        expense_id,
        amount
    )

    send_email(
        email,
        subject,
        body
    )



