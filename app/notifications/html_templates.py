def expense_approved_html(
    employee_name,
    expense_id,
    amount
):

    subject = "Expense Approved"

    body = f"""
<!DOCTYPE html>

<html>

<head>

<style>

body{{
font-family:Arial;
background:#f5f5f5;
}}

.container{{
width:600px;
margin:auto;
background:white;
padding:30px;
border-radius:10px;
}}

.header{{
background:#1E88E5;
color:white;
padding:20px;
font-size:24px;
text-align:center;
}}

.success{{
color:green;
font-size:20px;
font-weight:bold;
}}

table{{
width:100%;
border-collapse:collapse;
}}

td{{
padding:10px;
border:1px solid #ddd;
}}

.footer{{
margin-top:20px;
font-size:12px;
color:gray;
text-align:center;
}}

</style>

</head>

<body>

<div class="container">

<div class="header">

Expense Management System

</div>

<br>

<div class="success">

✅ Expense Approved

</div>

<br>

Hello <b>{employee_name}</b>,

<br><br>

Your expense has been approved successfully.

<br><br>

<table>

<tr>

<td>Expense ID</td>

<td>{expense_id}</td>

</tr>

<tr>

<td>Amount</td>

<td>₹{amount}</td>

</tr>

<tr>

<td>Status</td>

<td style="color:green;">
Approved
</td>

</tr>

</table>

<br>

Thank you for using our Expense Management System.

<div class="footer">

© 2026 Expense Management

</div>

</div>

</body>

</html>

"""

    return subject, body