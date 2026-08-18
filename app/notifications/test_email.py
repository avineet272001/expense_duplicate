from app.notifications.email_service import send_email

send_email(
    to_email="pushkaran.tyagi@shilshatech.com",
    subject="Expense Management System",
    body="""
Hello Piyush,

Congratulations!

Your Notification Module is working successfully.

Regards,
Expense Management System
"""
)