from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.firebase.firebase_config import initialize_firebase

from app.database import engine, Base
import app.models

Base.metadata.create_all(bind=engine)

from app.routes.sub_vendor import (
    router as sub_vendor_router
)
from app.routes.expense import router as expense_router
from app.routes.dashboard import router as dashboard_router
from app.routes.reports import router as reports_router
from app.routes.admin import router as admin_router

from app.scheduler.scheduler import start_scheduler

from app.firebase.notifications import (
    router as notifications_router
)


app = FastAPI(
    title="Expense Management API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

# Employee-facing expense module
app.include_router(expense_router)

app.include_router(dashboard_router)

app.include_router(reports_router)


# Admin module
app.include_router(admin_router)


# Sub-vendor module
app.include_router(sub_vendor_router)


# Firebase notification module
app.include_router(notifications_router)


# ============================================================
# HOME
# ============================================================

@app.get("/api")
def home():

    return {
        "message": "Expense Management API Running Successfully"
    }


# ============================================================
# ADMIN FRONTEND
# ============================================================

app.mount(
    "/admin-ui",
    StaticFiles(
        directory="admin-frontend",
        html=True
    ),
    name="admin-frontend"
)


# ============================================================
# SUB-VENDOR FRONTEND
# ============================================================

app.mount(
    "/vendor-ui",
    StaticFiles(
        directory="sub-vendor-frontend",
        html=True
    ),
    name="sub-vendor-frontend"
)


# ============================================================
# EMPLOYEE FRONTEND
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory="frontend",
        html=True
    ),
    name="frontend"
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():

    initialize_firebase()

    start_scheduler()