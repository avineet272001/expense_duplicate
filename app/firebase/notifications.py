from fastapi import (
    APIRouter,
    HTTPException,
    Depends
)

from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import NotificationToken

from app.firebase.notification_service import (
    send_push_notification,
    send_notification_to_user
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


# ============================================================
# DATABASE
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class NotificationTokenRequest(BaseModel):

    user_id: int

    device_token: str


class NotificationTestRequest(BaseModel):

    device_token: str

    title: str

    body: str


# ============================================================
# REGISTER FCM TOKEN
# ============================================================

@router.post("/register-token")
def register_notification_token(
    request: NotificationTokenRequest,
    db: Session = Depends(get_db)
):

    existing_token = (
        db.query(NotificationToken)
        .filter(
            NotificationToken.device_token
            == request.device_token
        )
        .first()
    )

    if existing_token:

        existing_token.user_id = request.user_id
        existing_token.is_active = True

        db.commit()
        db.refresh(existing_token)

        return {
            "success": True,
            "message": "Notification token updated",
            "token_id": existing_token.id
        }

    notification_token = NotificationToken(

        user_id=request.user_id,

        device_token=request.device_token,

        is_active=True
    )

    db.add(notification_token)

    db.commit()

    db.refresh(notification_token)

    return {
        "success": True,
        "message": "Notification token registered",
        "token_id": notification_token.id
    }


# ============================================================
# TEST NOTIFICATION
# ============================================================

@router.post("/test")
def test_notification(
    request: NotificationTestRequest
):

    try:

        message_id = send_push_notification(

            device_token=request.device_token,

            title=request.title,

            body=request.body
        )

        return {

            "success": True,

            "message": (
                "Notification sent successfully"
            ),

            "message_id": message_id
        }

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )

# ============================================================
# TEST NOTIFICATION BY USER ID
# ============================================================

@router.post("/test-user")
def test_notification_to_user(
    user_id: int,
    title: str,
    body: str,
    db: Session = Depends(get_db)
):

    result = send_notification_to_user(
        db=db,
        user_id=user_id,
        title=title,
        body=body
    )

    return result
    