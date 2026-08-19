from datetime import date
from decimal import Decimal
from typing import List, Optional
from app.services.activity_service import (
    log_sub_vendor_activity
)
from app import crud, schemas, models
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Request,
)
from fastapi import Response, Cookie
from app.services.email_service import send_activity_email_safe
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import crud, schemas, models
from app.config import ADMIN_USER_ID
from app.firebase.notification_service import notify_safe


from app.services.auth_service import (
    create_access_token,
    get_sub_vendor_id_from_token
)




router = APIRouter(
    prefix="/sub-vendor",
    tags=["Sub-Vendor Management"]
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def get_current_sub_vendor(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("sub_vendor_token")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    vendor_id = get_sub_vendor_id_from_token(token)
    if not vendor_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    
    vendor = db.query(models.SubVendor).filter(
        models.SubVendor.id == vendor_id
    ).first()
    
    if not vendor:
        raise HTTPException(
            status_code=401,
            detail="Sub-vendor not found"
        )
    
    return vendor


@router.post("/login")
def sub_vendor_login(
    request: schemas.SubVendorLogin,
    response: Response,
    db: Session = Depends(get_db)
):

    vendor = (
        db.query(models.SubVendor)
        .filter(
            models.SubVendor.email == request.email
        )
        .first()
    )

    if vendor is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

   

    if not vendor.is_active:

        raise HTTPException(
            status_code=403,
            detail=(
                "You are not allowed to login. "
                "Your account has been deactivated "
                "by the administrator."
            )
        )

   

    if vendor.password_hash != request.password:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )



    access_token = create_access_token(
        vendor.id
    )

 

    response.set_cookie(
        key="sub_vendor_token",
        value=access_token,
        httponly=True,
        secure=False,      
        samesite="lax",
        max_age=60 * 60
    )

    return {
        "success": True,
        "message": "Sub-vendor login successful",
        "sub_vendor_id": vendor.id,
        "name": vendor.name,
        "email": vendor.email,
        "is_active": vendor.is_active
    }




# DATABASE


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()



# DASHBOARD


@router.get(
    "/dashboard",
    response_model=schemas.DashboardResponse
)
def sub_vendor_dashboard(
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)
):

    return crud.get_dashboard_summary(db)



# CATEGORIES - VIEW ONLY


@router.get(
    "/options",
    response_model=schemas.SubVendorOptionsResponse
)
def get_sub_vendor_options(
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)
):
    return {
        "categories": crud.get_all_categories(db),
        "subcategories": crud.get_all_subcategories(db),
        "payment_methods": crud.get_all_payment_methods(db)
    }


# SUBCATEGORIES BY CATEGORY - VIEW ONLY


@router.get(
    "/categories/{category_id}/subcategories",
    response_model=List[schemas.SubCategoryResponse]
)
def get_subcategories_by_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)
):

    return crud.get_subcategories_by_category(
        db,
        category_id
    )




@router.post(
    "/category-requests",
    response_model=schemas.CategoryRequestResponse
)
def create_category_request(
    request: schemas.CategoryRequestCreate,
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)

):

    category_request = crud.create_category_request(
        db=db,
        category_name=request.category_name,
        requested_by=request.requested_by,
        remarks=request.remarks
    )

   
    crud.create_sub_vendor_activity(
        db=db,
        user_id=request.requested_by,
        action="CREATE_CATEGORY_REQUEST",
        module="CATEGORY",
        record_id=category_request.id,
        description=(
            f"Requested category "
            f"'{request.category_name}'"
        ),
        status="SUCCESS"
    )

    send_activity_email_safe(
    subject="Sub-Vendor Activity - Category Request Created",
    body=f"""
    Sub-Vendor Activity Log

    Action: CREATE_CATEGORY_REQUEST
    Module: CATEGORY
    Category Request ID: {category_request.id}
    User ID: {request.requested_by}

    Category Name: {request.category_name}
    Request Status: PENDING
    Activity Status: SUCCESS

    Description:
    Requested category '{request.category_name}'.
     """
     )

    notify_safe(
        db=db,
        user_id=ADMIN_USER_ID,
        title="New category request",
        body=(
            f"Sub-vendor {request.requested_by} requested "
            f"category '{request.category_name}'"
        )
    )

    return category_request
   



# VIEW SUB-VENDOR'S CATEGORY REQUESTS


@router.get(
    "/category-requests",
    response_model=List[
        schemas.CategoryRequestResponse
    ]
)
def get_category_requests(
    requested_by: int,
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)
):

    return crud.get_category_requests_by_user(
        db=db,
        requested_by=requested_by
    )




@router.post(
    "/subcategory-requests",
    response_model=schemas.SubCategoryRequestResponse
)
def create_subcategory_request(
    request: schemas.SubCategoryRequestCreate,
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)

):

    subcategory_request = (
        crud.create_subcategory_request(
            db=db,
            category_id=request.category_id,
            subcategory_name=request.subcategory_name,
            requested_by=request.requested_by,
            remarks=request.remarks
        )
    )

    crud.create_sub_vendor_activity(
        db=db,
        user_id=request.requested_by,
        action="CREATE_SUBCATEGORY_REQUEST",
        module="SUBCATEGORY",
        record_id=subcategory_request.id,
        description=(
            f"Requested subcategory "
            f"'{request.subcategory_name}'"
        ),
        status="SUCCESS"
    )

    notify_safe(
        db=db,
        user_id=ADMIN_USER_ID,
        title="New subcategory request",
        body=(
            f"Sub-vendor {request.requested_by} requested "
            f"subcategory '{request.subcategory_name}'"
        )
    )

    return subcategory_request



@router.get(
    "/subcategory-requests",
    response_model=List[
        schemas.SubCategoryRequestResponse
    ]
)
def get_subcategory_requests(
    requested_by: int,
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)
):

    return crud.get_subcategory_requests_by_user(
        db=db,
        requested_by=requested_by
    )



# PAYMENT METHODS - VIEW ONLY


@router.get(
    "/payment-methods",
    response_model=List[
        schemas.PaymentMethodResponse
    ]
)
def get_payment_methods(
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)
):

    return crud.get_all_payment_methods(db)



# CREATE EXPENSE


@router.post(
    "/expenses",
    response_model=schemas.ExpenseResponse
)
def create_expense(

    expense_date: date = Form(...),

    title: str = Form(...),

    description: Optional[str] = Form(None),

    category_id: int = Form(...),

    subcategory_id: Optional[int] = Form(None),

    amount: Decimal = Form(...),

    payment_method: str = Form(...),

    created_by: int = Form(...),

    remarks: Optional[str] = Form(None),

    cheque_number: Optional[str] = Form(None),

    account_last_four: Optional[str] = Form(None),

    transaction_reference: Optional[str] = Form(None),

    bank_name: Optional[str] = Form(None),

    receipt: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)
):

    expense_data = schemas.ExpenseCreate(

        expense_date=expense_date,

        title=title,

        description=description,

        category_id=category_id,

        subcategory_id=subcategory_id,

        amount=amount,

        payment_method=payment_method,

        created_by=created_by,

        remarks=remarks,

        cheque_number=cheque_number,

        account_last_four=account_last_four,

        transaction_reference=transaction_reference,

        bank_name=bank_name,
    )


    created_expense = crud.create_expense(
        db,
        expense_data,
        receipt
    )


    crud.create_sub_vendor_activity(
        db=db,
        user_id=created_by,
        action="CREATE_EXPENSE",
        module="EXPENSE",
        record_id=created_expense.get("id"),
        description=(
            f"Created expense "
            f"'{title}' for amount {amount}"
        ),
        status="SUCCESS"
    )

    notify_safe(
        db=db,
        user_id=ADMIN_USER_ID,
        title="New expense submitted",
        body=(
            f"'{title}' for {amount} is waiting on your approval"
        )
    )

    return created_expense



# VIEW ALL EXPENSES


@router.get(
    "/expenses",
    response_model=List[schemas.ExpenseResponse]
)
def get_expenses(
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)
):

    return crud.get_all_expenses(db)



# VIEW SINGLE EXPENSE


@router.get(
    "/expenses/{expense_id}",
    response_model=schemas.ExpenseResponse
)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db)
):

    expense = crud.get_expense_by_id_serialized(
        db,
        expense_id
    )

    if expense is None:

        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    return expense



# UPDATE EXPENSE


@router.put(
    "/expenses/{expense_id}",
    response_model=schemas.ExpenseResponse
)
def update_expense(

    expense_id: int,

    expense: schemas.ExpenseUpdate,

    db: Session = Depends(get_db)
):


    existing_expense = crud.get_expense_by_id_serialized(
        db,
        expense_id
    )

    if existing_expense is None:

        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )


    updated = crud.update_expense(
        db,
        expense_id,
        expense
    )

    if updated is None:

        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )


    crud.create_sub_vendor_activity(
     db=db,
     user_id=existing_expense.get("created_by"),
     action="UPDATE_EXPENSE",
     module="EXPENSE",
     record_id=expense_id,
     description=(
        f"Updated expense "
        f"'{existing_expense.get('title', 'Expense')}'"
     ),
    status="SUCCESS"
     )

    return updated


# REJECT EXPENSE


@router.put(
    "/expenses/{expense_id}/status",
    response_model=schemas.ExpenseResponse
)
def update_expense_status(
    expense_id: int,
    status_data: schemas.ExpenseStatusUpdate,
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)
):
    if status_data.status != "Rejected":
        raise HTTPException(
            status_code=400,
            detail="Sub-vendor can only reject expenses"
        )

    expense = crud.reject_expense(
        db,
        expense_id,
        status_data.approved_by,
        status_data.remarks
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Expense not found "
                "or already processed"
            )
        )

    return expense


# PAYMENT REPORT


@router.get(
    "/reports/payments",
    response_model=List[
        schemas.PaymentReportResponse
    ]
)
def payment_report(
    payment_method_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_vendor = Depends(get_current_sub_vendor)
):

    return crud.get_payment_report(
        db,
        payment_method_id
    )


def get_current_sub_vendor(
    sub_vendor_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):

    if not sub_vendor_token:

        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    sub_vendor_id = get_sub_vendor_id_from_token(
        sub_vendor_token
    )

    vendor = (
        db.query(models.SubVendor)
        .filter(
            models.SubVendor.id == sub_vendor_id
        )
        .first()
    )

    if vendor is None:

        raise HTTPException(
            status_code=401,
            detail="Sub-vendor account not found"
        )

    # --------------------------------------------------------
    # ADMIN CAN DEACTIVATE ACCOUNT
    # --------------------------------------------------------

    if not vendor.is_active:

        raise HTTPException(
            status_code=403,
            detail=(
                "Your account has been deactivated "
                "by the administrator."
            )
        )

    return vendor