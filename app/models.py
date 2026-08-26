from sqlalchemy import (
 Column,
    Integer,
    String,
    Text,
    Date,
    Numeric,
    TIMESTAMP,
    ForeignKey,
    LargeBinary,
    Boolean,
    UniqueConstraint
)
from datetime import datetime

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base



# Expense Category


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    category_name = Column(
        String(100),
        unique=True,
        nullable=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    expenses = relationship(
        "Expense",
        back_populates="category"
    )

    subcategories = relationship(
        "ExpenseSubCategory",
        back_populates="category"
    )



# Expense


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    expense_number = Column(
        String(20),
        unique=True,
        nullable=False
    )

    expense_date = Column(
        Date,
        nullable=False
    )

    title = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text
    )

    category_id = Column(
        Integer,
        ForeignKey("expense_categories.id"),
        nullable=False
    )

    amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    payment_method = Column(
        String(30),
        nullable=False
    )

    receipt = Column(
        LargeBinary
    )

    receipt_name = Column(
        String(255)
    )

    receipt_type = Column(
        String(100)
    )

    status = Column(
        String(20),
        default="Pending"
    )

    created_by = Column(
        Integer,
        nullable=False
    )

    upi_paid_by = Column(
       Integer,
       nullable=True
     )

    approved_by = Column(
        Integer
    )

    approved_at = Column(
        TIMESTAMP
    )

    paid_at = Column(
        TIMESTAMP
    )

    remarks = Column(
        Text
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    receipt_image = Column(
        LargeBinary,
        nullable=True
    )

    subcategory_id = Column(
        Integer,
        ForeignKey("expense_subcategories.id"),
        nullable=True
    )


    category = relationship(
        "ExpenseCategory",
        back_populates="expenses"
    )

    subcategory = relationship(
        "ExpenseSubCategory",
        back_populates="expenses"
    )


    payments = relationship(
        "ExpensePayment",
        back_populates="expense"
    )

   
  


# Expense Subcategory


class ExpenseSubCategory(Base):
    __tablename__ = "expense_subcategories"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    category_id = Column(
        Integer,
        ForeignKey("expense_categories.id"),
        nullable=False
    )

    subcategory_name = Column(
        String(100),
        nullable=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    category = relationship(
        "ExpenseCategory",
        back_populates="subcategories"
    )

    expenses = relationship(
        "Expense",
        back_populates="subcategory"
    )



# Payment Method


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    payment_method_name = Column(
        String(50),
        unique=True,
        nullable=False
    )

    payments = relationship(
        "ExpensePayment",
        back_populates="payment_method"
    )



# Expense Payment


class ExpensePayment(Base):
    __tablename__ = "expense_payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Which expense was paid?
    expense_id = Column(
        Integer,
        ForeignKey("expenses.id"),
        nullable=False
    )

    # How was it paid?
    payment_method_id = Column(
        Integer,
        ForeignKey("payment_methods.id"),
        nullable=False
    )

    upi_paid_by = Column(
        Integer,
        nullable=True
    )



    # Used when payment method is Cheque
    cheque_number = Column(
        String(50),
        nullable=True
    )


    account_last_four = Column(
        String(4),
        nullable=True
    )

    transaction_reference = Column(
        String(100),
        nullable=True
    )

    # Bank involved in the payment
    bank_name = Column(
        String(100),
        nullable=True
    )

    payment_date = Column(
        TIMESTAMP,
        nullable=True
    )




    expense = relationship(
        "Expense",
        back_populates="payments"
    )

    payment_method = relationship(
        "PaymentMethod",
        back_populates="payments"
    )



# SUB-VENDOR CATEGORY REQUEST


class CategoryRequest(Base):
    __tablename__ = "category_requests"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    category_name = Column(
        String(150),
        nullable=False
    )

    requested_by = Column(
        Integer,
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="PENDING"
    )

    remarks = Column(
        Text,
        nullable=True
    )

    approved_by = Column(
        Integer,
        nullable=True
    )

    approved_at = Column(
        TIMESTAMP,
        nullable=True
    )

    rejection_reason = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )



# SUB-VENDOR SUBCATEGORY REQUEST


class SubCategoryRequest(Base):
    __tablename__ = "subcategory_requests"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    category_id = Column(
        Integer,
        nullable=False
    )

    subcategory_name = Column(
        String(150),
        nullable=False
    )

    requested_by = Column(
        Integer,
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="PENDING"
    )

    remarks = Column(
        Text,
        nullable=True
    )

    approved_by = Column(
        Integer,
        nullable=True
    )

    approved_at = Column(
        TIMESTAMP,
        nullable=True
    )

    rejection_reason = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )


# SUB VENDOR 

class SubVendor(Base):
    __tablename__ = "sub_vendors"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
    String(150),
    nullable=False
    )


    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    phone = Column(
        String(30),
        nullable=True
    )


    password_hash = Column(
        String(255),
        nullable=False
    )


    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )


    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )


    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    token_version = Column(
        Integer,
        nullable=False,
        default=0
    )

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    owner_type = Column(
        String(20),
        nullable=False,
        index=True
    )

    owner_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    balance = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    currency = Column(
        String(3),
        nullable=False,
        default="INR"
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "owner_type",
            "owner_id",
            name="uq_wallet_owner"
        ),
    )

    transactions = relationship(
        "WalletTransaction",
        back_populates="wallet"
    )


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    wallet_id = Column(
        Integer,
        ForeignKey("wallets.id"),
        nullable=False,
        index=True
    )

    transaction_type = Column(
        String(10),
        nullable=False
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False
    )

    balance_before = Column(
        Numeric(12, 2),
        nullable=False
    )

    balance_after = Column(
        Numeric(12, 2),
        nullable=False
    )

    reference_type = Column(
        String(50),
        nullable=True
    )

    reference_id = Column(
        Integer,
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    wallet = relationship(
        "Wallet",
        back_populates="transactions"
    )

    performed_by = Column(
    Integer,
    nullable=True,
    index=True
     )

# EMPLOYEE

class Employee(Base):
    __tablename__ = "employees"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    sub_vendor_id = Column(
        Integer,
        ForeignKey("sub_vendors.id"),
        nullable=False,
        index=True
    )

    name = Column(
        String(150),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    phone = Column(
        String(30),
        nullable=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    token_version = Column(
        Integer,
        nullable=False,
        default=0
    )

# SUB-VENDOR ACTIVITY LOG


class SubVendorActivityLog(Base):

    __tablename__ = "sub_vendor_activity_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    
    action = Column(
        String(100),
        nullable=False,
        index=True
    )

    
    module = Column(
        String(100),
        nullable=False,
        index=True
    )

    
    record_id = Column(
        Integer,
        nullable=True
    )

    
    description = Column(
        Text,
        nullable=True
    )

    
    status = Column(
        String(30),
        nullable=False,
        default="SUCCESS"
    )

    
    details = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )


# NOTIFICATION TOKEN


class NotificationToken(Base):

    __tablename__ = "notification_tokens"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    device_token = Column(
        String(500),
        nullable=False,
        unique=True,
        index=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )    

class Admin(Base):

    __tablename__ = "admins"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(50),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    phone = Column(
        String(30),
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    reset_token = Column(
        String(255),
        nullable=True
    )

    reset_token_expires_at = Column(
        String(255),
        nullable=True
    )

    token_version = Column(
        Integer,
        nullable=False,
        default=0
    )

class AuthSession(Base):
    __tablename__ = "auth_session"

    id = Column(
        Integer,
        primary_key=True,
        index = True,
    )

    user_id = Column(
        Integer,
        nullable=False,
        index = True
    )

    user_type = Column(
        String(30),
        nullable=False,
        index=True
    )

    jti = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    expires_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    revoked_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )



