from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import crud , schemas

router = APIRouter(
    prefix="/wallet",
    tags=["Wallet"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()    

@router.get(
    "/{owner_type}/{owner_id}",
    response_model=schemas.WalletDetailsResponse
)
def get_wallet_details(
    owner_type:str,
    owner_id:int,
    db:Session= Depends(get_db)
):
    wallet = crud.get_wallet(
        db,
        owner_type,
        owner_id
    )
    if wallet is None:
        raise HTTPException(
            status_code=404,
            detail="wallet Not Found"
        )
    transactions = crud.get_wallet_transactions(
        db,
        wallet.id
    )
    return {
        "wallet": wallet,
        "transactions": transactions
    }

@router.post(
    "/ {owner_type}/{owner_id}/transactions",
    response_model=schemas.WalletResponse
)
def create_wallet_transaction(
    owner_type:str,
    owner_id:int,
    data : schemas.WalletResponse,
    db:Session = Depends(get_db)
):
    try:
        if data.transaction_type == "CREDIT":
            return crud.credit_wallet(
                db=db,
                owner_type=owner_type,
                owner_id=owner_id,
                amount=data.amount,
                performed_by=data.performed_by,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                description=data.description
            )
        if data.transaction_type == "DEBIT":
            return crud.debit_wallet(
                db=db,
                owner_type=owner_type,
                owner_id=owner_id,
                amount=data.amount,
                performed_by=data.performed_by,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                description=data.description
            )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )    


   