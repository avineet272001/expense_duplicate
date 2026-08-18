from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import crud, schemas

router = APIRouter(
    prefix="/expenses",
    tags=["Expense Management"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/categories", response_model=list[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return crud.get_all_categories(db)


@router.get(
    "/subcategories",
    response_model=list[schemas.SubCategoryResponse]
)
def get_all_subcategories(db: Session = Depends(get_db)):
    return crud.get_all_subcategories(db)


@router.get(
    "/categories/{category_id}/subcategories",
    response_model=list[schemas.SubCategoryResponse]
)
def get_subcategories_by_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    return crud.get_subcategories_by_category(db, category_id)


@router.get(
    "/payment-methods",
    response_model=list[schemas.PaymentMethodResponse]
)
def get_payment_methods(
    db: Session = Depends(get_db)
):
    return crud.get_all_payment_methods(db)



@router.post(
    "/",
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

    # Payment details
    cheque_number: Optional[str] = Form(None),
    account_last_four: Optional[str] = Form(None),
    transaction_reference: Optional[str] = Form(None),
    bank_name: Optional[str] = Form(None),

    receipt: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    return crud.get_all_expenses(db)


@router.get(
    "/{expense_id}",
    response_model=schemas.ExpenseResponse
)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db)
):
    expense = crud.get_expense_by_id_serialized(db, expense_id)

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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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



