from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import UploadFile
from app import models, schemas
import os
import shutil
import base64
import uuid
from datetime import date, datetime, timedelta
from sqlalchemy import func
UPLOAD_DIR = "uploads/receipts"
os.makedirs(UPLOAD_DIR, exist_ok=True)
from app.models import SubVendor

def create_expense(
    db: Session,
    expense: schemas.ExpenseCreate,
    receipt: UploadFile = None
):
    """
    Create an expense.

    IMPORTANT:
    Creating an expense is not the same as making a payment.
    ExpensePayment is therefore NOT created here.

    The actual ExpensePayment record is created/updated by
    mark_as_paid() when the expense is actually paid.
    """

    receipt_bytes = None
    receipt_name = None
    receipt_type = None

    if receipt is not None and receipt.filename:
        receipt_bytes = receipt.file.read()
        receipt_name = receipt.filename
        receipt_type = receipt.content_type

    # ---------------------------------------------------------
    # Validate payment method before creating the expense
    # ---------------------------------------------------------

    payment_method = (
        db.query(models.PaymentMethod)
        .filter(
            func.lower(
                models.PaymentMethod.payment_method_name
            )
            == expense.payment_method.strip().lower()
        )
        .first()
    )

    if not payment_method:
        raise ValueError(
            f"Payment method '{expense.payment_method}' does not exist"
        )

    # ---------------------------------------------------------
    # Create expense
    # ---------------------------------------------------------

    db_expense = models.Expense(
        expense_number=(
            f"EXP-{int(datetime.now().timestamp())}-"
            f"{uuid.uuid4().hex[:4].upper()}"
        ),

        expense_date=expense.expense_date,
        title=expense.title,
        description=expense.description,

        category_id=expense.category_id,
        subcategory_id=expense.subcategory_id,

        amount=expense.amount,

        payment_method=payment_method.payment_method_name,

        created_by=expense.created_by,
        remarks=expense.remarks,

        status="Pending",

        receipt_image=receipt_bytes,
        receipt_name=receipt_name,
        receipt_type=receipt_type,
    )

    db.add(db_expense)

    try:
        db.commit()
        db.refresh(db_expense)

    except Exception:
        db.rollback()
        raise

    return serialize_expense(db_expense)

def serialize_expense(expense):
    if expense is None:
        return None

    if expense.receipt_image:
        image = base64.b64encode(expense.receipt_image).decode("utf-8")
    else:
        image = None

    return {
        "id": expense.id,
        "expense_number": expense.expense_number,
        "expense_date": expense.expense_date,
        "title": expense.title,
        "description": expense.description,
        "category_id": expense.category_id,
        "subcategory_id": expense.subcategory_id,
        "amount": expense.amount,
        "payment_method": expense.payment_method,
        "status": expense.status,
        "created_by": expense.created_by,
        "approved_by": expense.approved_by,
        "approved_at": expense.approved_at,
        "paid_at": expense.paid_at,
        "remarks": expense.remarks,
        "created_at": expense.created_at,
        "updated_at": expense.updated_at,
        "category": expense.category,
        "subcategory": expense.subcategory,
        "receipt_name": expense.receipt_name,
        "receipt_type": expense.receipt_type,
        "receipt_image": image
    }

def get_all_expenses(db: Session):

    expenses = db.query(models.Expense).options(
        joinedload(models.Expense.category),
        joinedload(models.Expense.subcategory)
    ).order_by(models.Expense.created_at.desc()).all()

    return [serialize_expense(expense) for expense in expenses]
def get_expense_by_id(db: Session, expense_id: int):

    return (

        db.query(models.Expense).options(
            joinedload(models.Expense.category),
            joinedload(models.Expense.subcategory)
        )

        .filter(models.Expense.id == expense_id)

        .first()

    )

def get_expense_by_id_serialized(db: Session, expense_id: int):
    return serialize_expense(get_expense_by_id(db, expense_id))

def update_expense(

    db: Session,

    expense_id: int,

    expense: schemas.ExpenseUpdate

):

    db_expense = get_expense_by_id(db, expense_id)

    if not db_expense:
        return None

    update_data = expense.model_dump(exclude_unset=True)

    for key, value in update_data.items():

        setattr(db_expense, key, value)

    db.commit()

    db.refresh(db_expense)

    return serialize_expense(db_expense)

def delete_expense(db: Session, expense_id: int):

    db_expense = get_expense_by_id(db, expense_id)

    if not db_expense:
        return False

    db.delete(db_expense)

    db.commit()

    return True

def get_expenses_by_status(

    db: Session,

    status: str

):

    return (

        db.query(models.Expense)

        .filter(models.Expense.status == status)

        .all()

    )

def get_expenses_by_category(

    db: Session,

    category_id: int

):

    return (

        db.query(models.Expense)

        .filter(models.Expense.category_id == category_id)

        .all()

    )

def approve_expense(

    db: Session,

    expense_id: int,

    manager_id: int

):

    expense = get_expense_by_id(db, expense_id)

    if not expense:
        return None

    if expense.status != "Pending":
        return None

    expense.status = "Approved"

    expense.approved_by = manager_id

    expense.approved_at = datetime.now()

    db.commit()

    db.refresh(expense)

    return serialize_expense(expense)

def reject_expense(

    db: Session,

    expense_id: int,

    manager_id: int,

    remarks: str

):

    expense = get_expense_by_id(db, expense_id)

    if not expense:
        return None

    if expense.status != "Pending":
        return None

    expense.status = "Rejected"

    expense.approved_by = manager_id

    expense.approved_at = datetime.now()

    expense.remarks = remarks

    db.commit()

    db.refresh(expense)

    return serialize_expense(expense)


def mark_as_paid(
    db: Session,
    expense_id: int,
    payment_data: schemas.ExpensePaid
):
    """
    Mark an approved expense as Paid and record the actual payment.

    A payment record is created here if one does not already exist.
    This ensures the payment report represents actual payments,
    not merely expenses that were created.
    """

    # ---------------------------------------------------------
    # 1. Find the expense
    # ---------------------------------------------------------

    expense = get_expense_by_id(db, expense_id)

    if not expense:
        return None

    # ---------------------------------------------------------
    # 2. Expense must be Approved before payment
    # ---------------------------------------------------------

    if expense.status != "Approved":
        return None

    # ---------------------------------------------------------
    # 3. Find selected payment method
    # ---------------------------------------------------------

    payment_method = (
        db.query(models.PaymentMethod)
        .filter(
            models.PaymentMethod.id
            == payment_data.payment_method_id
        )
        .first()
    )

    if not payment_method:
        raise ValueError(
            "Payment method not found"
        )

    method = (
        payment_method.payment_method_name
        .strip()
        .lower()
    )

    # ---------------------------------------------------------
    # 4. Validate payment-specific details
    # ---------------------------------------------------------

    # CHEQUE
    if method == "cheque":

        if not payment_data.cheque_number:
            raise ValueError(
                "Cheque number is required for cheque payment"
            )

        if not payment_data.bank_name:
            raise ValueError(
                "Bank name is required for cheque payment"
            )

    # CARD
    elif method in [
        "debit card",
        "credit card",
        "corporate card"
    ]:

        if not payment_data.account_last_four:
            raise ValueError(
                "Last 4 digits are required for card payment"
            )

        if (
            len(payment_data.account_last_four) != 4
            or not payment_data.account_last_four.isdigit()
        ):
            raise ValueError(
                "Last 4 digits must contain exactly 4 numbers"
            )

        if not payment_data.transaction_reference:
            raise ValueError(
                "Transaction reference is required for card payment"
            )

    # UPI / DIGITAL WALLET
    elif method in [
        "upi",
        "google pay",
        "phonepe",
        "amazon pay",
        "paytm wallet"
    ]:

        if not payment_data.transaction_reference:
            raise ValueError(
                "Transaction reference is required for digital payment"
            )

    # BANK PAYMENT
    elif method in [
        "bank account",
        "bank transfer",
        "net banking",
        "neft",
        "rtgs",
        "imps"
    ]:

        if not payment_data.bank_name:
            raise ValueError(
                "Bank name is required for bank payment"
            )

        if not payment_data.account_last_four:
            raise ValueError(
                "Account last 4 digits are required"
            )

        if (
            len(payment_data.account_last_four) != 4
            or not payment_data.account_last_four.isdigit()
        ):
            raise ValueError(
                "Account last 4 digits must contain exactly 4 numbers"
            )

        if not payment_data.transaction_reference:
            raise ValueError(
                "Transaction reference is required"
            )

    # ---------------------------------------------------------
    # 5. Find existing payment record, if any
    # ---------------------------------------------------------

    payment = (
        db.query(models.ExpensePayment)
        .filter(
            models.ExpensePayment.expense_id == expense_id
        )
        .first()
    )

    # ---------------------------------------------------------
    # 6. Create or update the actual payment record
    # ---------------------------------------------------------

    if payment is None:

        payment = models.ExpensePayment(
            expense_id=expense.id,
            payment_method_id=payment_data.payment_method_id,
            cheque_number=payment_data.cheque_number,
            account_last_four=payment_data.account_last_four,
            transaction_reference=payment_data.transaction_reference,
            bank_name=payment_data.bank_name,
            payment_date=(
                payment_data.payment_date
                if payment_data.payment_date
                else datetime.now()
            )
        )

        db.add(payment)

    else:

        payment.payment_method_id = (
            payment_data.payment_method_id
        )

        payment.cheque_number = (
            payment_data.cheque_number
        )

        payment.account_last_four = (
            payment_data.account_last_four
        )

        payment.transaction_reference = (
            payment_data.transaction_reference
        )

        payment.bank_name = (
            payment_data.bank_name
        )

        payment.payment_date = (
            payment_data.payment_date
            if payment_data.payment_date
            else datetime.now()
        )

    # ---------------------------------------------------------
    # 7. Keep the Expense payment method synchronized
    # ---------------------------------------------------------

    expense.payment_method = (
        payment_method.payment_method_name
    )

    # ---------------------------------------------------------
    # 8. Mark expense as Paid
    # ---------------------------------------------------------

    expense.status = "Paid"
    expense.paid_at = datetime.now()

    # ---------------------------------------------------------
    # 9. Save everything atomically
    # ---------------------------------------------------------

    try:

        db.commit()
        db.refresh(expense)

    except Exception:

        db.rollback()
        raise

    return serialize_expense(expense)

def _get_expenses_by_status_serialized(db: Session, status: str):

    expenses = (
        db.query(models.Expense)
        .options(
            joinedload(models.Expense.category),
            joinedload(models.Expense.subcategory)
        )
        .filter(models.Expense.status == status)
        .order_by(models.Expense.created_at.desc())
        .all()
    )

    return [serialize_expense(e) for e in expenses]

def get_expenses_by_status_filter(
    db: Session,
    status: str = None
):
    query = (
        db.query(models.Expense)
        .options(
            joinedload(models.Expense.category),
            joinedload(models.Expense.subcategory)
        )
    )

    if status:
        query = query.filter(
            models.Expense.status == status
        )

    expenses = (
        query
        .order_by(models.Expense.created_at.desc())
        .all()
    )

    return [
        serialize_expense(expense)
        for expense in expenses
    ]

def get_payments_by_method(db: Session, payment_method_id: int):
    from sqlalchemy import func as sqlfunc

    payment_method = (
        db.query(models.PaymentMethod)
        .filter(models.PaymentMethod.id == payment_method_id)
        .first()
    )

    if not payment_method:
        return None

    results = (
        db.query(models.ExpensePayment, models.Expense)
        .join(
            models.Expense,
            models.Expense.id == models.ExpensePayment.expense_id
        )
        .filter(
            models.ExpensePayment.payment_method_id == payment_method_id
        )
        .order_by(models.ExpensePayment.payment_date.desc())
        .all()
    )

    return [
        {
            "payment_id": payment.id,
            "expense_id": expense.id,
            "expense_number": expense.expense_number,
            "title": expense.title,
            "expense_date": expense.expense_date,
            "amount": expense.amount,
            "status": expense.status,
            "created_by": expense.created_by,
            "payment_method_id": payment_method.id,
            "payment_method_name": payment_method.payment_method_name,
            "cheque_number": payment.cheque_number,
            "account_last_four": payment.account_last_four,
            "transaction_reference": payment.transaction_reference,
            "bank_name": payment.bank_name,
            "payment_date": payment.payment_date,
            "remarks": expense.remarks,
        }
        for payment, expense in results
    ]

def update_payment_details(
    db: Session,
    expense_id: int,
    payment_update: schemas.ExpensePaymentUpdate
):
    payment = (
        db.query(models.ExpensePayment)
        .filter(models.ExpensePayment.expense_id == expense_id)
        .first()
    )

    if not payment:
        return None

    update_data = payment_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)

    return payment

def get_all_payment_methods(db: Session):
    return db.query(models.PaymentMethod).all()

def create_payment_method(
    db: Session,
    payment_method: schemas.PaymentMethodCreate
):
    name = payment_method.payment_method_name.strip()

    if not name:
        raise ValueError("Payment method name cannot be empty")

    existing = (
        db.query(models.PaymentMethod)
        .filter(
            func.lower(models.PaymentMethod.payment_method_name)
            == name.lower()
        )
        .first()
    )

    if existing:
        raise ValueError(
            f"Payment method '{name}' already exists"
        )

    new_method = models.PaymentMethod(payment_method_name=name)

    db.add(new_method)
    db.commit()
    db.refresh(new_method)

    return new_method

def get_all_categories(db: Session):
    return db.query(models.ExpenseCategory).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    name = category.category_name.strip()

    if not name:
        raise ValueError("Category name cannot be empty")

    existing = (
        db.query(models.ExpenseCategory)
        .filter(
            func.lower(models.ExpenseCategory.category_name)
            == name.lower()
        )
        .first()
    )

    if existing:
        raise ValueError(
            f"Category '{name}' already exists"
        )

    new_category = models.ExpenseCategory(category_name=name)

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category

def get_all_subcategories(db: Session):
    return db.query(models.ExpenseSubCategory).all()

def create_subcategory(db: Session, subcategory: schemas.SubCategoryCreate):
    name = subcategory.subcategory_name.strip()

    if not name:
        raise ValueError("Subcategory name cannot be empty")

    category = (
        db.query(models.ExpenseCategory)
        .filter(models.ExpenseCategory.id == subcategory.category_id)
        .first()
    )

    if not category:
        raise ValueError("Category not found")

    existing = (
        db.query(models.ExpenseSubCategory)
        .filter(
            models.ExpenseSubCategory.category_id
            == subcategory.category_id,
            func.lower(models.ExpenseSubCategory.subcategory_name)
            == name.lower()
        )
        .first()
    )

    if existing:
        raise ValueError(
            f"Subcategory '{name}' already exists under this category"
        )

    new_subcategory = models.ExpenseSubCategory(
        category_id=subcategory.category_id,
        subcategory_name=name
    )

    db.add(new_subcategory)
    db.commit()
    db.refresh(new_subcategory)

    return new_subcategory

def get_subcategories_by_category(db: Session, category_id: int):
    return (
        db.query(models.ExpenseSubCategory)
        .filter(models.ExpenseSubCategory.category_id == category_id)
        .all()
    )

def get_dashboard_summary(db: Session):
    from sqlalchemy import func as sqlfunc

    total = db.query(models.Expense).count()
    pending = db.query(models.Expense).filter(models.Expense.status == "Pending").count()
    approved = db.query(models.Expense).filter(models.Expense.status == "Approved").count()
    rejected = db.query(models.Expense).filter(models.Expense.status == "Rejected").count()
    paid = db.query(models.Expense).filter(models.Expense.status == "Paid").count()
    total_amount = db.query(sqlfunc.coalesce(sqlfunc.sum(models.Expense.amount), 0)).scalar()

    return {
        "total_expenses": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "paid": paid,
        "total_amount": total_amount,
    }

def get_report_by_category(db: Session):
    from sqlalchemy import func as sqlfunc

    results = (
        db.query(
            models.ExpenseCategory.category_name,
            sqlfunc.coalesce(sqlfunc.sum(models.Expense.amount), 0)
        )
        .outerjoin(models.Expense, models.Expense.category_id == models.ExpenseCategory.id)
        .group_by(models.ExpenseCategory.category_name)
        .order_by(models.ExpenseCategory.category_name)
        .all()
    )

    return [
        {"category_name": name, "total_amount": total}
        for name, total in results
    ]

def get_category_subcategory_period_report(
    db: Session,
    start_date: date,
    end_date: date
):
    """
    Category and Subcategory expense report
    for the supplied date range.

    start_date and end_date are inclusive.
    """

    

    category_rows = (
        db.query(
            models.ExpenseCategory.id.label(
                "category_id"
            ),

            models.ExpenseCategory.category_name.label(
                "category_name"
            ),

            func.count(
                models.Expense.id
            ).label(
                "expense_count"
            ),

            func.coalesce(
                func.sum(models.Expense.amount),
                0
            ).label(
                "total_amount"
            )
        )

        .outerjoin(
            models.Expense,
            (
                models.Expense.category_id
                == models.ExpenseCategory.id
            )
            &
            (
                models.Expense.expense_date
                >= start_date
            )
            &
            (
                models.Expense.expense_date
                <= end_date
            )
        )

        .group_by(
            models.ExpenseCategory.id,
            models.ExpenseCategory.category_name
        )

        .order_by(
            models.ExpenseCategory.category_name
        )

        .all()
    )

  

    subcategory_rows = (
        db.query(
            models.ExpenseSubCategory.id.label(
                "subcategory_id"
            ),

            models.ExpenseSubCategory.category_id.label(
                "category_id"
            ),

            models.ExpenseSubCategory.subcategory_name.label(
                "subcategory_name"
            ),

            models.ExpenseCategory.category_name.label(
                "category_name"
            ),

            func.count(
                models.Expense.id
            ).label(
                "expense_count"
            ),

            func.coalesce(
                func.sum(models.Expense.amount),
                0
            ).label(
                "total_amount"
            )
        )

        .join(
            models.ExpenseCategory,
            models.ExpenseCategory.id
            == models.ExpenseSubCategory.category_id
        )

        .outerjoin(
            models.Expense,
            (
                models.Expense.subcategory_id
                == models.ExpenseSubCategory.id
            )
            &
            (
                models.Expense.expense_date
                >= start_date
            )
            &
            (
                models.Expense.expense_date
                <= end_date
            )
        )

        .group_by(
            models.ExpenseSubCategory.id,
            models.ExpenseSubCategory.category_id,
            models.ExpenseSubCategory.subcategory_name,
            models.ExpenseCategory.category_name
        )

        .order_by(
            models.ExpenseCategory.category_name,
            models.ExpenseSubCategory.subcategory_name
        )

        .all()
    )

    return {
        "category_report": [
            {
                "category_id": row.category_id,
                "category_name": row.category_name,
                "expense_count": row.expense_count,
                "total_amount": row.total_amount
            }
            for row in category_rows
        ],

        "subcategory_report": [
            {
                "subcategory_id": row.subcategory_id,
                "category_id": row.category_id,
                "category_name": row.category_name,
                "subcategory_name": row.subcategory_name,
                "expense_count": row.expense_count,
                "total_amount": row.total_amount
            }
            for row in subcategory_rows
        ]
    }

def get_payment_method_report(db: Session):
    from sqlalchemy import func as sqlfunc

    results = (
        db.query(
            models.PaymentMethod.id.label("payment_method_id"),
            models.PaymentMethod.payment_method_name.label(
                "payment_method_name"
            ),
            sqlfunc.count(
                models.ExpensePayment.id
            ).label("payment_count"),
            sqlfunc.coalesce(
                sqlfunc.sum(models.Expense.amount),
                0
            ).label("total_amount")
        )
        .join(
            models.ExpensePayment,
            models.ExpensePayment.payment_method_id
            == models.PaymentMethod.id
        )
        .join(
            models.Expense,
            models.Expense.id
            == models.ExpensePayment.expense_id
        )
        .group_by(
            models.PaymentMethod.id,
            models.PaymentMethod.payment_method_name
        )
        .order_by(
            models.PaymentMethod.payment_method_name
        )
        .all()
    )

    return [
        {
            "payment_method_id": row.payment_method_id,
            "payment_method_name": row.payment_method_name,
            "payment_count": row.payment_count,
            "total_amount": row.total_amount
        }
        for row in results
    ]

def get_payment_report(
    db: Session,
    payment_method_id: int = None
):
    query = (
        db.query(
            models.Expense.id.label("expense_id"),
            models.Expense.expense_number,
            models.Expense.title,
            models.Expense.amount,
            models.Expense.created_by,

            models.PaymentMethod.id.label(
                "payment_method_id"
            ),

            models.PaymentMethod.payment_method_name,

            models.ExpensePayment.cheque_number,
            models.ExpensePayment.account_last_four,
            models.ExpensePayment.transaction_reference,
            models.ExpensePayment.bank_name,
            models.ExpensePayment.payment_date,
        )
        .join(
            models.ExpensePayment,
            models.ExpensePayment.expense_id
            == models.Expense.id
        )
        .join(
            models.PaymentMethod,
            models.PaymentMethod.id
            == models.ExpensePayment.payment_method_id
        )
    )

    # Optional payment-method filter
    if payment_method_id is not None:
        query = query.filter(
            models.ExpensePayment.payment_method_id
            == payment_method_id
        )

    results = (
        query
        .order_by(
            models.ExpensePayment.payment_date.desc()
        )
        .all()
    )

    return [
        {
            "expense_id": row.expense_id,
            "expense_number": row.expense_number,
            "title": row.title,
            "amount": row.amount,
            "created_by": row.created_by,

            "payment_method_id": row.payment_method_id,
            "payment_method_name": row.payment_method_name,

            "cheque_number": row.cheque_number,
            "account_last_four": row.account_last_four,
            "transaction_reference": (
                row.transaction_reference
            ),
            "bank_name": row.bank_name,
            "payment_date": row.payment_date,
        }
        for row in results
    ]

def get_payment_report_date_range(
    period: str,
    report_date: date
):
    """
    Calculate the date range for the payment report.

    Supported periods:
        - daily
        - monthly
    """

    period = period.lower().strip()

    if period == "daily":

        start_date = report_date
        end_date = report_date

    elif period == "monthly":

        start_date = report_date.replace(day=1)

        if report_date.month == 12:

            next_month = date(
                report_date.year + 1,
                1,
                1
            )

        else:

            next_month = date(
                report_date.year,
                report_date.month + 1,
                1
            )

        end_date = next_month - timedelta(days=1)

    else:

        raise ValueError(
            "Invalid period. Use daily or monthly."
        )

    return start_date, end_date

def get_report_date_range(
    period: str,
    report_date: date
):
    """
    Calculate date range for reports.

    Supported:
        daily
        weekly
        monthly
    """

    period = period.lower().strip()

    # --------------------------------------------------------
    # DAILY
    # --------------------------------------------------------

    if period == "daily":

        start_date = report_date
        end_date = report_date

    # --------------------------------------------------------
    # WEEKLY
    # Monday -> Sunday
    # --------------------------------------------------------

    elif period == "weekly":

        start_date = (
            report_date
            - timedelta(
                days=report_date.weekday()
            )
        )

        end_date = start_date + timedelta(days=6)

    # --------------------------------------------------------
    # MONTHLY
    # --------------------------------------------------------

    elif period == "monthly":

        start_date = report_date.replace(
            day=1
        )

        if report_date.month == 12:

            next_month = date(
                report_date.year + 1,
                1,
                1
            )

        else:

            next_month = date(
                report_date.year,
                report_date.month + 1,
                1
            )

        end_date = (
            next_month
            - timedelta(days=1)
        )

    else:

        raise ValueError(
            "Invalid period. "
            "Use daily, weekly, or monthly."
        )

    return start_date, end_date

def get_payment_period_report(
    db: Session,
    start_date: date,
    end_date: date,
):
    """
    Return payment totals grouped by payment method.

    Rules:
        1. Show every payment method.
        2. Count only actual ExpensePayment records.
        3. Count only payments whose payment_date is inside
           the requested date range.
        4. Count only payments belonging to Paid expenses.
        5. Payment methods with no payments return zero.
    """

    payment_date_start = start_date
    payment_date_end = end_date + timedelta(days=1)

    results = (
        db.query(
            models.PaymentMethod.id.label(
                "payment_method_id"
            ),

            models.PaymentMethod.payment_method_name.label(
                "payment_method_name"
            ),

            # Count the Expense row, not ExpensePayment.
            # This prevents unpaid payment records from being
            # counted when the Expense join is NULL.
            func.count(
                models.Expense.id
            ).label(
                "payment_count"
            ),

            func.coalesce(
                func.sum(
                    models.Expense.amount
                ),
                0
            ).label(
                "total_amount"
            )
        )

   

        .outerjoin(
            models.ExpensePayment,
            (
                models.ExpensePayment.payment_method_id
                == models.PaymentMethod.id
            )
            &
            (
                models.ExpensePayment.payment_date
                >= payment_date_start
            )
            &
            (
                models.ExpensePayment.payment_date
                < payment_date_end
            )
        )


        .outerjoin(
            models.Expense,
            (
                models.Expense.id
                == models.ExpensePayment.expense_id
            )
            &
            (
                models.Expense.status == "Paid"
            )
        )

        .group_by(
            models.PaymentMethod.id,
            models.PaymentMethod.payment_method_name
        )

        .order_by(
            models.PaymentMethod.payment_method_name
        )

        .all()
    )

    return [
        {
            "payment_method_id":
                row.payment_method_id,

            "payment_method_name":
                row.payment_method_name,

            "payment_count":
                row.payment_count,

            "total_amount":
                row.total_amount
        }
        for row in results
    ]

def get_payment_custom_report(
    db: Session,
    start_date: date,
    end_date: date
):
    """
    Payment report for a custom date range.
    """

    if start_date > end_date:
        raise ValueError(
            "start_date cannot be greater than end_date"
        )

    return get_payment_period_report(
        db=db,
        start_date=start_date,
        end_date=end_date
    )


def create_category_request(
    db: Session,
    category_name: str,
    requested_by: int,
    remarks: str = None
):
    """
    Create a category approval request.

    IMPORTANT:
    This does NOT create the actual category.

    It only creates a PENDING request.
    """

    

    existing_category = (
        db.query(models.ExpenseCategory)
        .filter(
            func.lower(
                models.ExpenseCategory.category_name
            )
            ==
            category_name.strip().lower()
        )
        .first()
    )

    if existing_category:

        raise ValueError(
            "Category already exists."
        )


    existing_request = (
        db.query(models.CategoryRequest)
        .filter(
            func.lower(
                models.CategoryRequest.category_name
            )
            ==
            category_name.strip().lower(),

            models.CategoryRequest.status
            == "PENDING"
        )
        .first()
    )

    if existing_request:

        raise ValueError(
            "A pending request for this category "
            "already exists."
        )


    category_request = models.CategoryRequest(

        category_name=category_name.strip(),

        requested_by=requested_by,

        status="PENDING",

        remarks=remarks
    )

    db.add(category_request)

    db.commit()

    db.refresh(category_request)

    return category_request

def get_category_requests_by_user(
    db: Session,
    requested_by: int
):
    """
    Return category requests created by
    a particular Sub-Vendor.
    """

    return (
        db.query(models.CategoryRequest)
        .filter(
            models.CategoryRequest.requested_by
            == requested_by
        )
        .order_by(
            models.CategoryRequest.created_at.desc()
        )
        .all()
    )


def create_subcategory_request(
    db: Session,
    category_id: int,
    subcategory_name: str,
    requested_by: int,
    remarks: str = None
):
    """
    Create a subcategory approval request.

    IMPORTANT:
    This does NOT create the actual subcategory.

    It only creates a PENDING request.
    """

    
    category = (
        db.query(models.ExpenseCategory)
        .filter(
            models.ExpenseCategory.id
            == category_id
        )
        .first()
    )

    if category is None:

        raise ValueError(
            "Category not found."
        )

    existing_subcategory = (
        db.query(models.ExpenseSubCategory)
        .filter(
            models.ExpenseSubCategory.category_id
            == category_id,

            func.lower(
                models.ExpenseSubCategory.subcategory_name
            )
            ==
            subcategory_name.strip().lower()
        )
        .first()
    )

    if existing_subcategory:

        raise ValueError(
            "Subcategory already exists."
        )

    existing_request = (
        db.query(models.SubCategoryRequest)
        .filter(
            models.SubCategoryRequest.category_id
            == category_id,

            func.lower(
                models.SubCategoryRequest.subcategory_name
            )
            ==
            subcategory_name.strip().lower(),

            models.SubCategoryRequest.status
            == "PENDING"
        )
        .first()
    )

    if existing_request:

        raise ValueError(
            "A pending request for this "
            "subcategory already exists."
        )

    subcategory_request = (
        models.SubCategoryRequest(

            category_id=category_id,

            subcategory_name=(
                subcategory_name.strip()
            ),

            requested_by=requested_by,

            status="PENDING",

            remarks=remarks
        )
    )

    db.add(subcategory_request)

    db.commit()

    db.refresh(subcategory_request)

    return subcategory_request

def get_subcategory_requests_by_user(
    db: Session,
    requested_by: int
):
    """
    Return subcategory requests created by
    a particular Sub-Vendor.
    """

    return (
        db.query(models.SubCategoryRequest)
        .filter(
            models.SubCategoryRequest.requested_by
            == requested_by
        )
        .order_by(
            models.SubCategoryRequest.created_at.desc()
        )
        .all()
    )



def get_all_category_requests(
    db: Session,
    status: str = None
):
    """
    Get all category requests.

    If status is supplied, return only requests
    having that status.
    """

    query = (
        db.query(models.CategoryRequest)
    )

    if status:
        query = query.filter(
            models.CategoryRequest.status
            == status.upper()
        )

    return (
        query
        .order_by(
            models.CategoryRequest.created_at.desc()
        )
        .all()
    )

def approve_category_request(
    db: Session,
    request_id: int,
    approved_by: int
):
    """
    Approve a category request.

    Steps:

    1. Find request
    2. Make sure it is PENDING
    3. Check category doesn't already exist
    4. Create actual category
    5. Mark request APPROVED
    """

    category_request = (
        db.query(models.CategoryRequest)
        .filter(
            models.CategoryRequest.id
            == request_id
        )
        .first()
    )

    if category_request is None:

        raise ValueError(
            "Category request not found."
        )

    if category_request.status != "PENDING":

        raise ValueError(
            "Only PENDING requests can be approved."
        )

   

    existing_category = (
        db.query(models.ExpenseCategory)
        .filter(
            func.lower(
                models.ExpenseCategory.category_name
            )
            ==
            category_request.category_name
            .strip()
            .lower()
        )
        .first()
    )

    if existing_category:

        raise ValueError(
            "This category already exists."
        )


    new_category = models.ExpenseCategory(
        category_name=(
            category_request.category_name
            .strip()
        )
    )

    db.add(new_category)

    category_request.status = "APPROVED"

    category_request.approved_by = approved_by

    category_request.approved_at = func.now()

    category_request.rejection_reason = None

    db.commit()

    db.refresh(category_request)

    return category_request

def reject_category_request(
    db: Session,
    request_id: int,
    rejected_by: int,
    rejection_reason: str
):
    """
    Reject a category request.
    """

    category_request = (
        db.query(models.CategoryRequest)
        .filter(
            models.CategoryRequest.id
            == request_id
        )
        .first()
    )

    if category_request is None:

        raise ValueError(
            "Category request not found."
        )

    if category_request.status != "PENDING":

        raise ValueError(
            "Only PENDING requests can be rejected."
        )

    category_request.status = "REJECTED"

    category_request.approved_by = rejected_by

    category_request.rejection_reason = (
        rejection_reason.strip()
    )

    category_request.approved_at = func.now()

    db.commit()

    db.refresh(category_request)

    return category_request



def get_all_subcategory_requests(
    db: Session,
    status: str = None
):
    """
    Get all subcategory requests.
    """

    query = (
        db.query(
            models.SubCategoryRequest
        )
    )

    if status:

        query = query.filter(
            models.SubCategoryRequest.status
            == status.upper()
        )

    return (
        query
        .order_by(
            models.SubCategoryRequest.created_at.desc()
        )
        .all()
    )

def approve_subcategory_request(
    db: Session,
    request_id: int,
    approved_by: int
):
    """
    Approve a subcategory request.

    Steps:

    1. Find request
    2. Check PENDING
    3. Check parent category
    4. Check duplicate subcategory
    5. Create actual subcategory
    6. Mark request APPROVED
    """

    subcategory_request = (
        db.query(
            models.SubCategoryRequest
        )
        .filter(
            models.SubCategoryRequest.id
            == request_id
        )
        .first()
    )

    if subcategory_request is None:

        raise ValueError(
            "Subcategory request not found."
        )

    if subcategory_request.status != "PENDING":

        raise ValueError(
            "Only PENDING requests can be approved."
        )

   

    category = (
        db.query(
            models.ExpenseCategory
        )
        .filter(
            models.ExpenseCategory.id
            == subcategory_request.category_id
        )
        .first()
    )

    if category is None:

        raise ValueError(
            "Parent category not found."
        )

 

    existing_subcategory = (
        db.query(
            models.ExpenseSubCategory
        )
        .filter(
            models.ExpenseSubCategory.category_id
            == subcategory_request.category_id,

            func.lower(
                models.ExpenseSubCategory
                .subcategory_name
            )
            ==
            subcategory_request
            .subcategory_name
            .strip()
            .lower()
        )
        .first()
    )

    if existing_subcategory:

        raise ValueError(
            "This subcategory already exists."
        )

 

    new_subcategory = (
        models.ExpenseSubCategory(

            category_id=(
                subcategory_request.category_id
            ),

            subcategory_name=(
                subcategory_request
                .subcategory_name
                .strip()
            )
        )
    )

    db.add(new_subcategory)

  

    subcategory_request.status = "APPROVED"

    subcategory_request.approved_by = approved_by

    subcategory_request.approved_at = func.now()

    subcategory_request.rejection_reason = None

    db.commit()

    db.refresh(subcategory_request)

    return subcategory_request

def reject_subcategory_request(
    db: Session,
    request_id: int,
    rejected_by: int,
    rejection_reason: str
):
    """
    Reject a subcategory request.
    """

    subcategory_request = (
        db.query(
            models.SubCategoryRequest
        )
        .filter(
            models.SubCategoryRequest.id
            == request_id
        )
        .first()
    )

    if subcategory_request is None:

        raise ValueError(
            "Subcategory request not found."
        )

    if subcategory_request.status != "PENDING":

        raise ValueError(
            "Only PENDING requests can be rejected."
        )

    subcategory_request.status = "REJECTED"

    subcategory_request.approved_by = rejected_by

    subcategory_request.rejection_reason = (
        rejection_reason.strip()
    )

    subcategory_request.approved_at = func.now()

    db.commit()

    db.refresh(subcategory_request)

    return subcategory_request



def create_sub_vendor_activity(
    db: Session,
    user_id: int,
    action: str,
    module: str,
    record_id: int = None,
    description: str = None,
    status: str = "SUCCESS",
    details: str = None,
):
    """
    Create an activity log for a Sub-Vendor action.
    """

    activity = models.SubVendorActivityLog(

        user_id=user_id,

        action=action,

        module=module,

        record_id=record_id,

        description=description,

        status=status,

        details=details,
    )

    db.add(activity)

    db.commit()

    db.refresh(activity)

    return activity

def get_sub_vendor_activities(
    db: Session,
    user_id: int = None,
    module: str = None,
    action: str = None,
):
    """
    Get Sub-Vendor activity logs.

    Filters are optional.
    """

    query = db.query(
        models.SubVendorActivityLog
    )

    if user_id is not None:

        query = query.filter(
            models.SubVendorActivityLog.user_id
            == user_id
        )

    if module:

        query = query.filter(
            models.SubVendorActivityLog.module
            == module
        )

    if action:

        query = query.filter(
            models.SubVendorActivityLog.action
            == action
        )

    return (
        query
        .order_by(
            models.SubVendorActivityLog.created_at.desc()
        )
        .all()
    )



def create_sub_vendor(
    db: Session,
    sub_vendor,
    password_hash: str
):

    existing = (
        db.query(SubVendor)
        .filter(
            SubVendor.email == sub_vendor.email
        )
        .first()
    )

    if existing:

        raise ValueError(
            "A sub-vendor with this email already exists"
        )

    vendor = SubVendor(

        name=sub_vendor.name,

        email=sub_vendor.email,

        phone=sub_vendor.phone,

        password_hash=password_hash,

        is_active=True
    )

    db.add(vendor)

    db.commit()

    db.refresh(vendor)

    return vendor

def get_all_sub_vendors(db: Session):

    return (
        db.query(SubVendor)
        .order_by(SubVendor.id.desc())
        .all()
    )

def get_sub_vendor(
    db: Session,
    sub_vendor_id: int
):

    return (
        db.query(SubVendor)
        .filter(
            SubVendor.id == sub_vendor_id
        )
        .first()
    )

def update_sub_vendor(
    db: Session,
    sub_vendor_id: int,
    data,
    password_hash: str = None
):

    vendor = get_sub_vendor(
        db,
        sub_vendor_id
    )

    if vendor is None:
        return None

    if data.name is not None:
        vendor.name = data.name

    if data.email is not None:
        vendor.email = data.email

    if data.phone is not None:
        vendor.phone = data.phone

    if password_hash is not None:
        vendor.password_hash = password_hash

    db.commit()

    db.refresh(vendor)

    return vendor

def activate_sub_vendor(
    db: Session,
    sub_vendor_id: int
):

    vendor = get_sub_vendor(
        db,
        sub_vendor_id
    )

    if vendor is None:
        return None

    vendor.is_active = True

    db.commit()

    db.refresh(vendor)

    return vendor

def deactivate_sub_vendor(
    db: Session,
    sub_vendor_id: int
):

    vendor = get_sub_vendor(
        db,
        sub_vendor_id
    )

    if vendor is None:
        return None

    vendor.is_active = False

    db.commit()

    db.refresh(vendor)

    return vendor

def delete_sub_vendor(
    db: Session,
    sub_vendor_id: int
):

    vendor = get_sub_vendor(
        db,
        sub_vendor_id
    )

    if vendor is None:
        return None

    db.delete(vendor)

    db.commit()

    return vendor


def get_category_subcategory_period_report(
    db: Session,
    start_date: date,
    end_date: date
):
    end_datetime = end_date + timedelta(days=1)

    results = (
        db.query(
            # ----------------------------------------------------
            # CATEGORY
            # ----------------------------------------------------
            models.ExpenseCategory.id.label(
                "category_id"
            ),

            models.ExpenseCategory.category_name.label(
                "category_name"
            ),

            # ----------------------------------------------------
            # SUBCATEGORY
            # ----------------------------------------------------
            models.ExpenseSubCategory.id.label(
                "subcategory_id"
            ),

            models.ExpenseSubCategory.subcategory_name.label(
                "subcategory_name"
            ),

            # ----------------------------------------------------
            # TOTALS
            # ----------------------------------------------------
            func.count(
                models.Expense.id
            ).label(
                "expense_count"
            ),

            func.coalesce(
                func.sum(
                    models.Expense.amount
                ),
                0
            ).label(
                "total_amount"
            )
        )

        # --------------------------------------------------------
        # CATEGORY -> EXPENSE
        # --------------------------------------------------------
        .join(
            models.Expense,
            models.Expense.category_id
            == models.ExpenseCategory.id
        )

        # --------------------------------------------------------
        # EXPENSE -> SUBCATEGORY
        # --------------------------------------------------------
        .outerjoin(
            models.ExpenseSubCategory,
            models.Expense.subcategory_id
            == models.ExpenseSubCategory.id
        )

        # --------------------------------------------------------
        # DATE FILTER
        # --------------------------------------------------------
        .filter(
            models.Expense.expense_date >= start_date,
            models.Expense.expense_date < end_datetime
        )

        # --------------------------------------------------------
        # GROUPING
        # --------------------------------------------------------
        .group_by(
            models.ExpenseCategory.id,
            models.ExpenseCategory.category_name,

            models.ExpenseSubCategory.id,
            models.ExpenseSubCategory.subcategory_name
        )

        # --------------------------------------------------------
        # ORDER
        # --------------------------------------------------------
        .order_by(
            models.ExpenseCategory.category_name,
            models.ExpenseSubCategory.subcategory_name
        )

        .all()
    )

    return [
        {
            "category_id": row.category_id,

            "category_name": row.category_name,

            "subcategory_id": row.subcategory_id,

            "subcategory_name": (
                row.subcategory_name
                if row.subcategory_name
                else "No Subcategory"
            ),

            "expense_count": row.expense_count,

            "total_amount": row.total_amount,
        }

        for row in results
    ]

