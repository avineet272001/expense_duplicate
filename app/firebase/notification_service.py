import logging

from firebase_admin import messaging

logger = logging.getLogger(__name__)


def send_push_notification(
    device_token: str,
    title: str,
    body: str
):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=device_token
    )

    response = messaging.send(message)

    return response





def send_notification_to_user(
    db,
    user_id: int,
    title: str,
    body: str
):

    from app.models import NotificationToken

    token = (
        db.query(NotificationToken)
        .filter(
            NotificationToken.user_id == user_id,
            NotificationToken.is_active == True
        )
        .first()
    )

    if token is None:

        return {
            "success": False,
            "message": "No active notification token found"
        }

    try:

        message_id = send_push_notification(

            device_token=token.device_token,

            title=title,

            body=body
        )

        return {
            "success": True,
            "message": "Notification sent successfully",
            "message_id": message_id
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }




def notify_safe(
    db,
    user_id: int,
    title: str,
    body: str
):

    try:

        return send_notification_to_user(
            db=db,
            user_id=user_id,
            title=title,
            body=body
        )

    except Exception as e:

        logger.warning(
            "Push notification to user %s failed: %s",
            user_id,
            e
        )

        return {
            "success": False,
            "message": str(e)
        }