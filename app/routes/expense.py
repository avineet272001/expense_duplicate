from datetime import date
from decimal import Decimal
from typing import List, Optional
from datetime import date, datetime, timezone
from jose import JWTError, jwt
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Response,
    Request,
)
import uuid
from app.services.auth_service import (
    SECRET_KEY,
    ALGORITHM
)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import crud, schemas, models
from app.services.auth_service import create_access_token

from app.services.auth_service import (
    get_employee_id_from_token,
    create_employee_access_token,
)

router = APIRouter(
    prefix="/expenses",
    tags=["Employee Management"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# async def get_current_employee(
#         request: Request,
#         db: Session = Depends(get_db)
# ):
#     token =  request.cookies.get("employee_token")
#     if not token:
#         raise HTTPException(
#             status_code=401,
#             detail="Employee authentication required"
#         )
#     employee_id = get_employee_id_from_token(token)
#     employee = (
#         db.query(models.Employee)
#         .filter(
#             models.Employee.id == employee_id
#         )
#         .first()
#     )

#     if employee is None:
#         raise HTTPException(
#             status_code=401,
#             detail="Employee not found"
#         )
#         if not employee.is_active:
#          raise HTTPException(
#             status_code=403,
#             detail="Employee account is deactivated"
#         )

#     return employee


async def get_current_employee(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("employee_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Employee authentication required"
        )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        employee_id = payload.get("sub")
        jti = payload.get("jti")
        user_type = payload.get("type")

        if employee_id is None or jti is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

        if user_type != "employee":
            raise HTTPException(
                status_code=403,
                detail="Invalid employee token"
            )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    session = (
        db.query(models.AuthSession)
        .filter(
            models.AuthSession.jti == jti,
            models.AuthSession.user_id == int(employee_id),
            models.AuthSession.user_type == "employee"
        )
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid session"
        )

    if session.revoked_at is not None:
        raise HTTPException(
            status_code=401,
            detail="Session has been revoked"
        )

    if session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=401,
            detail="Session has expired"
        )

    employee = (
        db.query(models.Employee)
        .filter(
            models.Employee.id == int(employee_id)
        )
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=401,
            detail="Employee not found"
        )

    if not employee.is_active:
        raise HTTPException(
            status_code=403,
            detail="Employee account is deactivated"
        )

    return employee

# @router.post("/login")
# async def employee_login(
#     request: schemas.EmployeeLogin,
#     response: Response,
#     db: Session = Depends(get_db)
# ):
    

#     employee = (
#         db.query(models.Employee)
#         .filter(
#             models.Employee.email == request.email
#         )
#         .first()
#     )

#     if employee is None:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid email or password"
#         )


    

#     if not employee.is_active:
#         raise HTTPException(
#             status_code=403,
#             detail=(
#                 "You are not allowed to login. "
#                 "Your account has been deactivated "
#                 "by the sub-vendor."
#             )
#         )


    

#     if employee.password_hash != request.password:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid email or password"
#         )


    

#     access_token = create_employee_access_token(
#         employee.id
#     )


    

#     response.set_cookie(
#         key="employee_token",
#         value=access_token,
#         httponly=True,
#         secure=False,
#         samesite="lax",
#         max_age=60 * 60
#     )


    

#     return {
#         "success": True,
#         "message": "Employee login successful",
#         "employee_id": employee.id,
#         "sub_vendor_id": employee.sub_vendor_id,
#         "name": employee.name,
#         "email": employee.email,
#         "is_active": employee.is_active
#     }

@router.post("/login")
def employee_login(
    request: schemas.EmployeeLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    employee = (
        db.query(models.Employee)
        .filter(
            models.Employee.email == request.email
        )
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not employee.is_active:
        raise HTTPException(
            status_code=403,
            detail=(
                "You are not allowed to login. "
                "Your account has been deactivated "
                "by the sub-vendor."
            )
        )

    if employee.password_hash != request.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create unique session ID
    jti = str(uuid.uuid4())

    # Create JWT
    access_token, expires_at = create_employee_access_token(
        employee.id,
        jti
    )

    # Create database session
    auth_session = models.AuthSession(
        user_id=employee.id,
        user_type="employee",
        jti=jti,
        expires_at=expires_at
    )

    db.add(auth_session)
    db.commit()

    # Store token in browser
    response.set_cookie(
        key="employee_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60
    )

    return {
        "success": True,
        "message": "Employee login successful",
        "employee_id": employee.id,
        "sub_vendor_id": employee.sub_vendor_id,
        "name": employee.name,
        "email": employee.email,
        "is_active": employee.is_active
    }
@router.get(
    "/options",
    response_model=schemas.ExpenseOptionsResponse
)
async def get_expense_options(
    db: Session = Depends(get_db),
    current_employee_id: int = Depends(get_current_employee)
    
):
    return {
        "categories": crud.get_all_categories(db),
        "subcategories": crud.get_all_subcategories(db),
        "payment_methods": crud.get_all_payment_methods(db),
        "employees": crud.get_all_employees(db)
    }

@router.post(
    "/",
    response_model=schemas.ExpenseResponse
)
async def create_expense(
    expense_date: date = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),

    category_id: int = Form(...),
    subcategory_id: Optional[int] = Form(None),

    amount: Decimal = Form(...),

    payment_method: str = Form(...),
    upi_paid_by: Optional[int] = Form(None),

    created_by: int = Form(...),
    
    remarks: Optional[str] = Form(None),

    # Payment details
    cheque_number: Optional[str] = Form(None),
    account_last_four: Optional[str] = Form(None),
    transaction_reference: Optional[str] = Form(None),
    bank_name: Optional[str] = Form(None),

    receipt: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db),
    current_employee_id: int = Depends(get_current_employee)
):
    expense_data = schemas.ExpenseCreate(
        expense_date=expense_date,
        title=title,
        description=description,

        category_id=category_id,
        subcategory_id=subcategory_id,

        amount=amount,

        payment_method=payment_method,
        upi_paid_by=upi_paid_by,

        created_by=created_by,
        remarks=remarks,

        # Payment details
        cheque_number=cheque_number,
        account_last_four=account_last_four,
        transaction_reference=transaction_reference,
        bank_name=bank_name,
    )

    return crud.create_expense(
        db,
        expense_data,
        receipt
    )


@router.get(
    "/",
    response_model=List[schemas.ExpenseResponse]
)
def get_expenses(
    db: Session = Depends(get_db),
    current_employee = Depends(get_current_employee)
    
):
    return crud.get_all_expenses(db,current_employee.id)


@router.get(
    "/{expense_id}",
    response_model=schemas.ExpenseResponse
)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_employee = Depends(get_current_employee)
):
    expense = crud.get_expense_by_id_serialized(db, expense_id, current_employee.id)

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    return expense


@router.put(
    "/{expense_id}",
    response_model=schemas.ExpenseResponse
)
def update_expense(
    expense_id: int,
    expense: schemas.ExpenseUpdate,
    db: Session = Depends(get_db),
    current_employee = Depends(get_current_employee)
):
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

    return updated


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_employee = Depends(get_current_employee)
):
    deleted = crud.delete_expense(
        db,
        expense_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    return {
        "message": "Expense deleted successfully"
    }

@router.post("/logout")
def employee_logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_employee = Depends(get_current_employee)
):
    token = request.cookies.get("employee_token")

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )

    jti = payload.get("jti")

    session = (
        db.query(models.AuthSession)
        .filter(
            models.AuthSession.jti == jti,
            models.AuthSession.user_id == current_employee.id,
            models.AuthSession.user_type == "employee"
        )
        .first()
    )

    if session:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()

    response.delete_cookie("employee_token")

    return {
        "success": True,
        "message": "Employee logout successful"
    }



