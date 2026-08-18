from app.notifications.service import send_expense_approved_email

send_expense_approved_email(
    email="shreya.singh@shilshatech.com",
    employee_name="Piyush Rai",
    expense_id="EXP-1001",
    amount=2500
)