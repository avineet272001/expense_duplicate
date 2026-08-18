from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import crud, schemas
from datetime import date
from typing import List, Optional
from fastapi.responses import StreamingResponse
from app.models import SubVendor
from app.services.payment_report_pdf import (
    generate_payment_report_pdf
)
from app.firebase.notification_service import notify_safe

router = APIRouter(
    prefix="/admin",
    tags=["Admin Management"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# CATEGORY & SUBCATEGORY MANAGEMENT
# ============================================================

@router.post(
    "/categories",
    response_model=schemas.CategoryResponse
)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db)
):
    try:
        return crud.create_category(db, category)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@router.post(
    "/subcategories",
    response_model=schemas.SubCategoryResponse
)
def create_subcategory(
    subcategory: schemas.SubCategoryCreate,
    db: Session = Depends(get_db)
):
    try:
        return crud.create_subcategory(db, subcategory)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


# ============================================================
# PAYMENT METHODS
# ============================================================

@router.get(
    "/payment-methods",
    response_model=List[schemas.PaymentMethodResponse]
)
def payment_methods(
    db: Session = Depends(get_db)
):
    return crud.get_all_payment_methods(db)


@router.post(
    "/payment-methods",
    response_model=schemas.PaymentMethodResponse
)
def create_payment_method(
    payment_method: schemas.PaymentMethodCreate,
    db: Session = Depends(get_db)
):
    try:
        return crud.create_payment_method(db, payment_method)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


# ============================================================
# EXPENSE/PAYMENT DETAILS BY PAYMENT METHOD
# ============================================================

@router.get(
    "/payment-methods/{payment_method_id}/details",
    response_model=List[schemas.ExpensePaymentDetailResponse]
)
def payment_method_details(
    payment_method_id: int,
    db: Session = Depends(get_db)
):
    details = crud.get_payments_by_method(db, payment_method_id)

    if details is None:
        raise HTTPException(
            status_code=404,
            detail="Payment method not found"
        )

    return details


# ============================================================
# UPDATE / ADD PAYMENT DETAILS (e.g. correcting a cheque number)
# ============================================================

@router.put(
    "/expenses/{expense_id}/payment-details",
    response_model=schemas.ExpensePaymentResponse
)
def update_payment(
    expense_id: int,
    payment_update: schemas.ExpensePaymentUpdate
    
    ,
    db: Session = Depends(get_db)
):
    payment = crud.update_payment_details(
        db,
        expense_id,
        payment_update
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="No payment record found for this expense"
        )

    return payment


# ============================================================
# DASHBOARD
# ============================================================

@router.get(
    "/dashboard",
    response_model=schemas.DashboardResponse
)
def dashboard(
    db: Session = Depends(get_db)
):
    return crud.get_dashboard_summary(db)


# ============================================================
# EXPENSE LISTS
# ============================================================

@router.get(
    "/expenses/pending",
    response_model=List[schemas.ExpenseResponse]
)
def pending_expenses(
    db: Session = Depends(get_db)
):
    return crud.get_pending_expenses(db)


@router.get(
    "/expenses/approved",
    response_model=List[schemas.ExpenseResponse]
)
def approved_expenses(
    db: Session = Depends(get_db)
):
    return crud.get_approved_expenses(db)


@router.get(
    "/expenses/rejected",
    response_model=List[schemas.ExpenseResponse]
)
def rejected_expenses(
    db: Session = Depends(get_db)
):
    return crud.get_rejected_expenses(db)


@router.get(
    "/expenses/paid",
    response_model=List[schemas.ExpenseResponse]
)
def paid_expenses(
    db: Session = Depends(get_db)
):
    return crud.get_paid_expenses(db)


# ============================================================
# APPROVE EXPENSE
# ============================================================

@router.put(
    "/expenses/{expense_id}/approve",
    response_model=schemas.ExpenseResponse
)
def approve_expense(
    expense_id: int,
    approval: schemas.ExpenseApproval,
    db: Session = Depends(get_db)
):

    expense = crud.approve_expense(
        db,
        expense_id,
        approval.approved_by
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense not found or already processed"
        )

    notify_safe(
      db=db,
      user_id=expense["created_by"],
      title="Expense approved",
      body=f"Your expense '{expense.get('title', 'Expense')}' was approved"
    )

    return expense


# ============================================================
# REJECT EXPENSE
# ============================================================

@router.put(
    "/expenses/{expense_id}/reject",
    response_model=schemas.ExpenseResponse
)
def reject_expense(
    expense_id: int,
    rejection: schemas.ExpenseReject,
    db: Session = Depends(get_db)
):

    expense = crud.reject_expense(
        db,
        expense_id,
        rejection.approved_by,
        rejection.remarks
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense not found or already processed"
        )

    notify_safe(
       db=db,
     user_id=expense["created_by"],
     title="Expense rejected",
     body=(
        f"Your expense "
        f"'{expense.get('title', 'Expense')}' "
        f"was rejected: "
        f"{rejection.remarks}"
     )
    )

    return expense


# ===============================================
# MARK EXPENSE AS PAID
# ===============================================

@router.put(
    "/expenses/{expense_id}/paid",
    response_model=schemas.ExpenseResponse
)
def mark_as_paid(
    expense_id: int,
    payment: schemas.ExpensePaid,
    db: Session = Depends(get_db)
):

 

    try:
        expense = crud.mark_as_paid(
            db,
            expense_id,
            payment
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Expense not approved, "
                "payment method not found, "
                "or expense not found"
            )
        )

    notify_safe(
         db=db,
     user_id=expense["created_by"],
     title="Expense paid",
     body=(
        f"Your expense "
        f"'{expense.get('title', 'Expense')}' "
        f"has been paid out"
    )
    )

    return expense



@router.get(
    "/reports/payment-methods",
    response_model=List[schemas.PaymentMethodReportResponse]
)
def payment_method_report(
    db: Session = Depends(get_db)
):

    return crud.get_payment_method_report(db)


@router.get(
    "/reports/payments",
    response_model=List[schemas.PaymentReportResponse]
)
def payment_report(
    payment_method_id: int = None,
    db: Session = Depends(get_db)
):
    return crud.get_payment_report(
        db,
        payment_method_id
    )

@router.get(
    "/payment-report",
    response_model=List[
        schemas.PaymentPeriodReportResponse
    ]
)
def payment_report(
    period: str = "monthly",
    report_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    if report_date is None:
        report_date = date.today()

    period = period.lower().strip()

    if period not in [
        "daily",
        "weekly",
        "monthly"
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "period must be daily, "
                "weekly, or monthly"
            )
        )

    try:
        start_date, end_date = (
            crud.get_payment_report_date_range(
                period,
                report_date
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return crud.get_payment_period_report(
        db=db,
        start_date=start_date,
        end_date=end_date,
        
    )

@router.get(
    "/payment-report",
    response_model=List[
        schemas.PaymentMethodReportResponse
    ]
)
def payment_report(
    period: str = "monthly",
    report_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Payment report grouped by payment method.

    Supported periods:
        daily
        weekly
        monthly
    """

    # If date is not provided,
    # use today's date.
    if report_date is None:
        report_date = date.today()

    period = period.lower().strip()

    if period not in [
        "daily",
        "weekly",
        "monthly"
    ]:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid period. "
                "Use daily, weekly, or monthly."
            )
        )

    try:

        start_date, end_date = (
            crud.get_payment_report_date_range(
                period,
                report_date
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return crud.get_payment_period_report(
        db=db,
        start_date=start_date,
        end_date=end_date
    )


@router.get(
    "/payment-report/custom",
    response_model=List[
        schemas.PaymentMethodReportResponse
    ]
)
def custom_payment_report(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """
    Payment report for a custom date range.
    """

    if start_date > end_date:

        raise HTTPException(
            status_code=400,
            detail=(
                "start_date cannot be greater "
                "than end_date."
            )
        )

    return crud.get_payment_custom_report(
        db=db,
        start_date=start_date,
        end_date=end_date
    )


@router.get(
    "/payment-report/pdf"
)
def payment_report_pdf(
    period: str = "monthly",
    report_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Download payment method report as PDF.
    """

    if report_date is None:
        report_date = date.today()

    period = period.lower().strip()

    if period not in [
        "daily",
        "weekly",
        "monthly"
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid period. "
                "Use daily, weekly, or monthly."
            )
        )

    try:

        start_date, end_date = (
            crud.get_payment_report_date_range(
                period,
                report_date
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


    report_rows = crud.get_payment_period_report(
        db=db,
        start_date=start_date,
        end_date=end_date
    )




    pdf_file = generate_payment_report_pdf(
        report_rows=report_rows,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    filename = (
        f"payment_report_"
        f"{start_date}_"
        f"{end_date}.pdf"
    )

    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        }
    )


@router.get(
    "/payment-report/custom",
    response_model=List[
        schemas.PaymentMethodReportResponse
    ]
)
def custom_payment_report(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """
    Payment report for a custom date range.
    """

    if start_date > end_date:

        raise HTTPException(
            status_code=400,
            detail=(
                "start_date cannot be greater "
                "than end_date"
            )
        )

    return crud.get_payment_custom_report(
        db=db,
        start_date=start_date,
        end_date=end_date
    )



# ============================================================
# SUB-VENDOR CATEGORY REQUESTS
# ============================================================


@router.get(
    "/category-requests",
    response_model=List[
        schemas.CategoryRequestResponse
    ]
)
def get_category_requests(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Admin can view all category requests.

    Optional:
        ?status=PENDING
        ?status=APPROVED 
        ?status=REJECTED
    """

    return crud.get_all_category_requests(
        db=db,
        status=status
    )


# ============================================================
# APPROVE CATEGORY REQUEST
# ============================================================

@router.put(
    "/category-requests/{request_id}/approve",
    response_model=schemas.CategoryRequestResponse
)
def approve_category_request(
    request_id: int,
    approval: schemas.CategoryRequestApproval,
    db: Session = Depends(get_db)
):

    try:

        result = crud.approve_category_request(
            db=db,
            request_id=request_id,
            approved_by=approval.approved_by
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    notify_safe(
        db=db,
        user_id=result.requested_by,
        title="Category request approved",
        body=f"Your category request '{result.category_name}' was approved"
    )

    return result


# ============================================================
# REJECT CATEGORY REQUEST
# ============================================================

@router.put(
    "/category-requests/{request_id}/reject",
    response_model=schemas.CategoryRequestResponse
)
def reject_category_request(
    request_id: int,
    rejection: schemas.CategoryRequestRejection,
    db: Session = Depends(get_db)
):

    try:

        result = crud.reject_category_request(
            db=db,
            request_id=request_id,
            rejected_by=rejection.rejected_by,
            rejection_reason=(
                rejection.rejection_reason
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    notify_safe(
        db=db,
        user_id=result.requested_by,
        title="Category request rejected",
        body=(
            f"Your category request '{result.category_name}' "
            f"was rejected: {rejection.rejection_reason}"
        )
    )

    return result


# ============================================================
# SUB-VENDOR SUBCATEGORY REQUESTS
# ============================================================


@router.get(
    "/subcategory-requests",
    response_model=List[
        schemas.SubCategoryRequestResponse
    ]
)
def get_subcategory_requests(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Admin can view all subcategory requests.
    """

    return crud.get_all_subcategory_requests(
        db=db,
        status=status
    )


# ============================================================
# APPROVE SUBCATEGORY REQUEST
# ============================================================

@router.put(
    "/subcategory-requests/{request_id}/approve",
    response_model=schemas.SubCategoryRequestResponse
)
def approve_subcategory_request(
    request_id: int,
    approval: schemas.SubCategoryRequestApproval,
    db: Session = Depends(get_db)
):

    try:

        result = crud.approve_subcategory_request(
            db=db,
            request_id=request_id,
            approved_by=approval.approved_by
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    notify_safe(
        db=db,
        user_id=result.requested_by,
        title="Subcategory request approved",
        body=f"Your subcategory request '{result.subcategory_name}' was approved"
    )

    return result


# ============================================================
# REJECT SUBCATEGORY REQUEST
# ============================================================

@router.put(
    "/subcategory-requests/{request_id}/reject",
    response_model=schemas.SubCategoryRequestResponse
)
def reject_subcategory_request(
    request_id: int,
    rejection: schemas.SubCategoryRequestRejection,
    db: Session = Depends(get_db)
):

    try:

        result = crud.reject_subcategory_request(
            db=db,
            request_id=request_id,
            rejected_by=rejection.rejected_by,
            rejection_reason=(
                rejection.rejection_reason
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    notify_safe(
        db=db,
        user_id=result.requested_by,
        title="Subcategory request rejected",
        body=(
            f"Your subcategory request '{result.subcategory_name}' "
            f"was rejected: {rejection.rejection_reason}"
        )
    )

    return result

@router.get(
    "/sub-vendor-activities",
    response_model=List[
        schemas.SubVendorActivityResponse
    ]
)
def get_sub_vendor_activities(
    user_id: Optional[int] = None,
    module: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db)
):

    return crud.get_sub_vendor_activities(
        db=db,
        user_id=user_id,
        module=module,
        action=action,
    )

# ============================================================
# SUB-VENDOR MANAGEMENT
# ============================================================

@router.get(
    "/sub-vendors",
    response_model=List[schemas.SubVendorResponse]
)
def get_sub_vendors(
    db: Session = Depends(get_db)
):
    return crud.get_all_sub_vendors(db)


@router.get(
    "/sub-vendors/{sub_vendor_id}",
    response_model=schemas.SubVendorResponse
)
def get_sub_vendor(
    sub_vendor_id: int,
    db: Session = Depends(get_db)
):

    vendor = crud.get_sub_vendor(
        db,
        sub_vendor_id
    )

    if vendor is None:
        raise HTTPException(
            status_code=404,
            detail="Sub-vendor not found"
        )

    return vendor

@router.post(
    "/sub-vendors",
    response_model=schemas.SubVendorResponse
)
def create_sub_vendor(
    request: schemas.SubVendorCreate,
    db: Session = Depends(get_db)
):

    try:

        vendor = crud.create_sub_vendor(
            db=db,
            sub_vendor=request,
            password_hash=request.password
        )

        return vendor

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.put(
    "/sub-vendors/{sub_vendor_id}",
    response_model=schemas.SubVendorResponse
)
def update_sub_vendor(
    sub_vendor_id: int,
    request: schemas.SubVendorUpdate,
    db: Session = Depends(get_db)
):

    vendor = crud.get_sub_vendor(
        db,
        sub_vendor_id
    )

    if vendor is None:
        raise HTTPException(
            status_code=404,
            detail="Sub-vendor not found"
        )

    updated = crud.update_sub_vendor(
        db=db,
        sub_vendor_id=sub_vendor_id,
        data=request
    )

    return updated

@router.put(
    "/sub-vendors/{sub_vendor_id}/activate",
    response_model=schemas.SubVendorResponse
)
def activate_sub_vendor(
    sub_vendor_id: int,
    db: Session = Depends(get_db)
):

    vendor = crud.activate_sub_vendor(
        db,
        sub_vendor_id
    )

    if vendor is None:
        raise HTTPException(
            status_code=404,
            detail="Sub-vendor not found"
        )

    return vendor

@router.put(
    "/sub-vendors/{sub_vendor_id}/deactivate",
    response_model=schemas.SubVendorResponse
)
def deactivate_sub_vendor(
    sub_vendor_id: int,
    db: Session = Depends(get_db)
):

    vendor = crud.deactivate_sub_vendor(
        db,
        sub_vendor_id
    )

    if vendor is None:
        raise HTTPException(
            status_code=404,
            detail="Sub-vendor not found"
        )

    return vendor


@router.delete(
    "/sub-vendors/{sub_vendor_id}"
)
def delete_sub_vendor(
    sub_vendor_id: int,
    db: Session = Depends(get_db)
):

    vendor = crud.delete_sub_vendor(
        db,
        sub_vendor_id
    )

    if vendor is None:
        raise HTTPException(
            status_code=404,
            detail="Sub-vendor not found"
        )

    return {
        "success": True,
        "message": "Sub-vendor deleted successfully",
        "id": sub_vendor_id
    }




@router.get(
    "/reports/category-subcategory",
    response_model=schemas.CategorySubCategoryPeriodReportResponse
)
def category_subcategory_report(
    period: str = "monthly",
    year: Optional[int] = None,
    month: Optional[int] = None,
    report_date: Optional[date] = None,
    db: Session = Depends(get_db)
):

    period = period.lower().strip()

    if period not in [
        "daily",
        "weekly",
        "monthly"
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid period. "
                "Use daily, weekly, or monthly."
            )
        )

    

    if period == "monthly":

        if year is None:
            year = date.today().year

        if month is None:
            month = date.today().month

        if month < 1 or month > 12:
            raise HTTPException(
                status_code=400,
                detail="month must be between 1 and 12"
            )

        try:

            report_date = date(
                year,
                month,
                1
            )

        except ValueError:

            raise HTTPException(
                status_code=400,
                detail="Invalid year or month"
            )



    else:

        if report_date is None:

            report_date = date.today()



    try:

        start_date, end_date = (
            crud.get_report_date_range(
                period,
                report_date
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


    report_rows = (
        crud.get_category_subcategory_period_report(
            db=db,
            start_date=start_date,
            end_date=end_date
        )
    )

    # ============================================================
    # BUILD CATEGORY REPORT
    # ============================================================

    category_data = {}

    for row in report_rows:

     category_id = row["category_id"]

    if category_id not in category_data:

        category_data[category_id] = {
            "category_id": category_id,
            "category_name": row["category_name"],
            "expense_count": 0,
            "total_amount": 0
        }

    category_data[
        category_id
    ]["expense_count"] += row["expense_count"]

    category_data[
        category_id
    ]["total_amount"] += row["total_amount"]

 

    subcategory_data = []

    for row in report_rows:

     subcategory_data.append({
        "category_id": row["category_id"],
        "category_name": row["category_name"],

        "subcategory_id": row["subcategory_id"],
        "subcategory_name": row["subcategory_name"],

        "expense_count": row["expense_count"],
        "total_amount": row["total_amount"]
    })

    return {
    "period": period,

    "start_date": start_date,

    "end_date": end_date,

    "category_report": list(
        category_data.values()
    ),

    "subcategory_report": subcategory_data
}

    

