"""
All email templates are stored here.
Each function returns (subject, body)
"""


def expense_created_template(employee_name, expense_id, amount):

    subject = "Expense Submitted Successfully"

    body = f"""
Hello {employee_name},

Your expense has been submitted successfully.

Expense ID : {expense_id}
Amount     : ₹{amount}

Current Status : Pending

Regards,
Expense Management Team
"""

    return subject, body


def expense_approved_template(employee_name, expense_id, amount):

    subject = "Expense Approved"

    body = f"""
Hello {employee_name},

Congratulations!

Your expense has been approved.

Expense ID : {expense_id}
Approved Amount : ₹{amount}

Regards,
Expense Management Team
"""

    return subject, body


def expense_rejected_template(employee_name, expense_id, remarks):

    subject = "Expense Rejected"

    body = f"""
Hello {employee_name},

Your expense has been rejected.

Expense ID : {expense_id}

Reason :

{remarks}

Regards,
Expense Management Team
"""

    return subject, body


def expense_paid_template(employee_name, expense_id, amount):

    subject = "Expense Paid"

    body = f"""
Hello {employee_name},

Payment has been processed successfully.

Expense ID : {expense_id}

Amount : ₹{amount}

Regards,
Finance Team
"""

    return subject, body