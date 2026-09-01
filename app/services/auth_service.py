from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from fastapi import HTTPException, status
import uuid
from fastapi import Request, HTTPException, status
SECRET_KEY = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
import secrets
import hashlib

def create_access_token(sub_vendor_id: int):

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(sub_vendor_id),
        "type": "sub_vendor",
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def get_sub_vendor_id_from_token(token: str):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        sub_vendor_id = payload.get("sub")

        if sub_vendor_id is None:
            raise credentials_exception

        if payload.get("type") != "sub_vendor":
            raise credentials_exception

        return int(sub_vendor_id)

    except (JWTError, ValueError):

        raise credentials_exception


def create_employee_access_token(
    employee_id: int,
    jti: str
):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(employee_id),
        "type": "employee",
        "jti": jti,
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token, expire


def get_employee_id_from_token(token: str):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        employee_id = payload.get("sub")

        if employee_id is None:
            raise credentials_exception

        if payload.get("type") != "employee":
            raise credentials_exception

        return int(employee_id)

    except (JWTError, ValueError):

        raise credentials_exception    

def get_current_employee(
        request:Request
):
    token = request.cookies.get("employee_token")

    if not token:
        raise HTTPException(
            status_code=404,
            detail="Employee Authenticatin required",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )
    return get_employee_id_from_token(token)


def create_admin_access_token(
    admin_id: int,
    jti: str
 ):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(admin_id),
        "type": "admin",
        "jti": jti,
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token, expire
def get_admin_id_from_token(
        token: str
        ):
        credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )
            admin_id = payload.get("sub")

            if admin_id is None:
                raise credentials_exception
            if payload.get("type") != "admin":
                raise credentials_exception

            return int(admin_id)
        except(JWTError,ValueError):
            raise credentials_exception



def get_current_admin(request: Request):

    token = request.cookies.get("admin_token")

    print("TOKEN FROM COOKIE:", token)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required"
        )

    admin_id = get_admin_id_from_token(token)

    print("ADMIN ID:", admin_id)

    return admin_id        

def generate_password_reset_token():
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()

    return token,token_hash

