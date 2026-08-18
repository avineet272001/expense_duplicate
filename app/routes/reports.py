from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import crud, schemas

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/by-category", response_model=list[schemas.ReportResponse])
def report_by_category(db: Session = Depends(get_db)):
    return crud.get_report_by_category(db)

