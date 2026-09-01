from app import crud

from app.services.email_service import (
    send_activity_email_safe
)


def log_sub_vendor_activity(
    db,
    user_id: int,
    action: str,
    module: str,
    record_id: int,
    description: str,
    status: str = "SUCCESS"
):



    activity = crud.create_sub_vendor_activity(
        db=db,
        user_id=user_id,
        action=action,
        module=module,
        record_id=record_id,
        description=description,
        status=status
    )



    email_subject = (
        f"Sub-Vendor Activity - {action}"
    )

    email_body = f"""
Sub-Vendor Activity Notification

User ID:
{user_id}

Action:
{action}

Module:
{module}

Record ID:
{record_id}

Description:
{description}

Status:
{status}
"""

    send_activity_email_safe(
        subject=email_subject,
        body=email_body
    )

    return activity