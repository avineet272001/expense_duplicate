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


# CATEGORY & SUBCATEGORY MANAGEMENT


@router.post("/categories")
def create_category_or_subcategory(
    data: schemas.CategoryManagementCreate,
    db: Session = Depends(get_db)
):
    try:

        
        # CREATE CATEGORY
        

        if data.type == "category":

            category = schemas.CategoryCreate(
                category_name=data.category_name
            )

            return crud.create_category(
                db,
                category
            )

        
        # CREATE SUBCATEGORY
        
        if data.type == "subcategory":

            if data.category_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="category_id is required for subcategory"
                )

            if not data.subcategory_name:
                raise HTTPException(
                    status_code=400,
                    detail="subcategory_name is required"
                )

            subcategory_data = schemas.SubCategoryCreate(
                category_id=data.category_id,
                subcategory_name=data.subcategory_name
            )

            return crud.create_subcategory(
                db,
                subcategory_data
            )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

# PAYMENT METHODS


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


# EXPENSE/PAYMENT DETAILS BY PAYMENT METHOD


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


# DASHBOARD


@router.get(
    "/dashboard",
    response_model=schemas.DashboardResponse
)
def dashboard(
    db: Session = Depends(get_db)
):
    return crud.get_dashboard_summary(db)

@router.get(
    "/expenses",
    response_model=List[schemas.ExpenseResponse]
)
def get_expenses(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return crud.get_expenses_by_status_filter(
        db,
        status
    )

@router.put(
    "/expenses/{expense_id}/status",
    response_model=schemas.ExpenseResponse
)
def update_expense_status(
    expense_id: int,
    update: schemas.ExpenseStatusUpdate,
    db: Session = Depends(get_db)
):
    if update.status == "Approved":

        if update.approved_by is None:
            raise HTTPException(
                status_code=400,
                detail="approved_by is required"
            )

        expense = crud.approve_expense(
            db,
            expense_id,
            update.approved_by
        )

        if expense is None:
            raise HTTPException(
                status_code=404,
                detail="Expense not found or already processed"
            )

        notify_safe(
            db=db,
            user_id=expense.created_by,
            title="Expense approved",
            body=f"Your expense '{expense.title}' was approved"
        )

        return expense

    if update.status == "Rejected":

        if update.approved_by is None:
            raise HTTPException(
                status_code=400,
                detail="approved_by is required"
            )

        if not update.remarks:
            raise HTTPException(
                status_code=400,
                detail="remarks is required"
            )

        expense = crud.reject_expense(
            db,
            expense_id,
            update.approved_by,
            update.remarks
        )

        if expense is None:
            raise HTTPException(
                status_code=404,
                detail="Expense not found or already processed"
            )

        notify_safe(
            db=db,
            user_id=expense.created_by,
            title="Expense rejected",
            body=(
                f"Your expense '{expense.title}' "
                f"was rejected: {update.remarks}"
            )
        )

        return expense

    if update.status == "Paid":

        if update.paid_by is None:
            raise HTTPException(
                status_code=400,
                detail="paid_by is required"
            )

        if update.payment_method_id is None:
            raise HTTPException(
                status_code=400,
                detail="payment_method_id is required"
            )

        payment = schemas.ExpensePaid(
            paid_by=update.paid_by,
            payment_method_id=update.payment_method_id,
            cheque_number=update.cheque_number,
            account_last_four=update.account_last_four,
            transaction_reference=update.transaction_reference,
            bank_name=update.bank_name,
            payment_date=update.payment_date,
            remarks=update.remarks
        )

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
            user_id=expense.created_by,
            title="Expense paid",
            body=f"Your expense '{expense.title}' has been paid out"
        )

        return expense



@router.post(
    "/wallet/transactions",
    response_model=schemas.WalletResponse
)
def admin_wallet_transaction(
    data: schemas.AdminWalletTransactionCreate,
    db: Session = Depends(get_db)
):
    try:
        if data.transaction_type == "CREDIT":
            return crud.credit_wallet(
                db=db,
                owner_type=data.owner_type,
                owner_id=data.owner_id,
                amount=data.amount,
                performed_by=data.performed_by,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                description=data.description
            )

        if data.transaction_type == "DEBIT":
            return crud.debit_wallet(
                db=db,
                owner_type=data.owner_type,
                owner_id=data.owner_id,
                amount=data.amount,
                performed_by=data.performed_by,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                description=data.description
            )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )



# PAYMENT REPORTS


@router.get("/reports/payments")
def payment_reports(
    report_type: str = "method",
    payment_method_id: Optional[int] = None,
    period: str = "monthly",
    report_date: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Payment reports.

    report_type:
        method  -> Payment method summary
        details -> Payment details
        period  -> Period-based payment report
        custom  -> Custom date-range payment report
    """

    report_type = report_type.lower().strip()

    
    # PAYMENT METHOD REPORT
    

    if report_type == "method":
        return crud.get_payment_method_report(db)

    
    # PAYMENT DETAILS
    

    if report_type == "details":
        return crud.get_payment_report(
            db=db,
            payment_method_id=payment_method_id
        )

    
    # PERIOD REPORT
    

    if report_type == "period":

        if report_date is None:
            report_date = date.today()

        period = period.lower().strip()

        if period not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=400,
                detail="period must be daily, weekly, or monthly"
            )

        try:
            report_start, report_end = (
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
            start_date=report_start,
            end_date=report_end
        )

    
    # CUSTOM DATE REPORT
    

    if report_type == "custom":

        if start_date is None or end_date is None:
            raise HTTPException(
                status_code=400,
                detail="start_date and end_date are required"
            )

        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be greater than end_date"
            )

        return crud.get_payment_custom_report(
            db=db,
            start_date=start_date,
            end_date=end_date
        )

    
    # INVALID REPORT TYPE
    

    raise HTTPException(
        status_code=400,
        detail=(
            "Invalid report_type. "
            "Use method, details, period, or custom."
        )
    )


# PAYMENT REPORT PDF


@router.get("/reports/payments/pdf")
def payment_report_pdf(
    period: str = "monthly",
    report_date: Optional[date] = None,
    db: Session = Depends(get_db)
):

    if report_date is None:
        report_date = date.today()

    period = period.lower().strip()

    if period not in ["daily", "weekly", "monthly"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid period. Use daily, weekly, or monthly."
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
        end_date=end_date
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


# SUB-VENDOR CATEGORY REQUESTS


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


# APPROVE CATEGORY REQUEST


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


# REJECT CATEGORY REQUEST


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


# SUB-VENDOR SUBCATEGORY REQUESTS


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


# APPROVE SUBCATEGORY REQUEST


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


# REJECT SUBCATEGORY REQUEST


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


# SUB-VENDOR MANAGEMENT


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
    "/sub-vendors/{sub_vendor_id}/status",
    response_model=schemas.SubVendorResponse
)
def update_sub_vendor_status(
    sub_vendor_id: int,
    status: schemas.SubVendorStatusUpdate,
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

    vendor.is_active = status.is_active

    db.commit()
    db.refresh(vendor)

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

    
    # BUILD CATEGORY REPORT
    

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


@router.post(
    "/wallet/transactions",
    response_model=schemas.WalletResponse
)
def admin_wallet_transaction(
    data: schemas.AdminWalletTransactionCreate,
    db: Session = Depends(get_db)
):
    try:

        if data.transaction_type == "CREDIT":

            return crud.credit_wallet(
                db=db,
                owner_type=data.owner_type,
                owner_id=data.owner_id,
                amount=data.amount,
                performed_by=data.performed_by,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                description=data.description
            )

        if data.transaction_type == "DEBIT":

            return crud.debit_wallet(
                db=db,
                owner_type=data.owner_type,
                owner_id=data.owner_id,
                amount=data.amount,
                performed_by=data.performed_by,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                description=data.description
            )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    


