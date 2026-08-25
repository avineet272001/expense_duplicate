from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from typing import Literal	
from pydantic import BaseModel, ConfigDict
from typing import List, Optional


# CATEGORY


class CategoryResponse(BaseModel):
    id: int
    category_name: str

    model_config = ConfigDict(from_attributes=True)

class CategoryCreate(BaseModel):
    category_name: str


# SUBCATEGORY


class SubCategoryResponse(BaseModel):
    id: int
    category_id: int
    subcategory_name: str

    model_config = ConfigDict(from_attributes=True)

class SubCategoryCreate(BaseModel):
    category_id: int
    subcategory_name: str

class CategoryManagementCreate(BaseModel):
    type: Literal["category", "subcategory"]

    category_name: Optional[str] = None
    category_id: Optional[int] = None
    subcategory_name: Optional[str] = None



# EXPENSE CREATE


class ExpenseCreate(BaseModel):
    expense_date: date
    title: str
    description: Optional[str] = None

    category_id: int
    subcategory_id: Optional[int] = None

    amount: Decimal
    
    payment_method: str

    created_by: int
    upi_paid_by: Optional[int] = None

    remarks: Optional[str] = None

    # Payment details
    cheque_number: Optional[str] = None
    account_last_four: Optional[str] = None
    transaction_reference: Optional[str] = None
    bank_name: Optional[str] = None


# EXPENSE UPDATE


class ExpenseUpdate(BaseModel):
    expense_date: Optional[date] = None

    title: Optional[str] = None

    description: Optional[str] = None

    category_id: Optional[int] = None

    subcategory_id: Optional[int] = None

    amount: Optional[Decimal] = None

    payment_method: Optional[str] = None

    remarks: Optional[str] = None


# EXPENSE RESPONSE


class ExpenseResponse(BaseModel):

    id: int

    expense_number: str

    expense_date: date

    title: str

    description: Optional[str] = None

    category: Optional[CategoryResponse] = None

    subcategory: Optional[SubCategoryResponse] = None

    amount: Decimal

    payment_method: str

    status: str

    created_by: int

    approved_by: Optional[int] = None

    approved_at: Optional[datetime] = None

    paid_at: Optional[datetime] = None

    remarks: Optional[str] = None

    created_at: datetime
    upi_paid_by: Optional[int] = None

    updated_at: datetime

    receipt_name: Optional[str] = None

    receipt_type: Optional[str] = None

    receipt_image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
    payment: Optional[ExpensePaymentResponse] = None


# EXPENSE APPROVAL


class ExpenseApproval(BaseModel):

    approved_by: int


# EXPENSE REJECTION


class ExpenseReject(BaseModel):

    approved_by: int

    remarks: str


# PAYMENT METHOD RESPONSE


class PaymentMethodResponse(BaseModel):

    id: int

    payment_method_name: str

    model_config = ConfigDict(from_attributes=True)

class ExpenseOptionsResponse(BaseModel):

    categories: list[CategoryResponse]

    subcategories: list[SubCategoryResponse]

    payment_methods: list[PaymentMethodResponse]    
    employees: List[EmployeeResponse]


class SubVendorOptionsResponse(BaseModel):

    categories: list[CategoryResponse]

    subcategories: list[SubCategoryResponse]

    payment_methods: list[PaymentMethodResponse]    

class PaymentReportResponse(BaseModel):
    expense_id: int
    expense_number: str
    title: str
    amount: Decimal

    created_by: int

    payment_method_id: int
    payment_method_name: str

    cheque_number: Optional[str] = None
    account_last_four: Optional[str] = None
    transaction_reference: Optional[str] = None
    bank_name: Optional[str] = None

    payment_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PaymentMethodCreate(BaseModel):

    payment_method_name: str


# EXPENSE PAYMENT CREATE


class ExpensePaymentCreate(BaseModel):

    expense_id: int

    payment_method_id: int

    cheque_number: Optional[str] = None

    account_last_four: Optional[str] = None

    transaction_reference: Optional[str] = None

    bank_name: Optional[str] = None

    payment_date: Optional[datetime] = None

    remarks: Optional[str] = None


# EXPENSE PAYMENT RESPONSE


class ExpensePaymentResponse(BaseModel):

    id: int

    expense_id: int

    payment_method_id: int

    cheque_number: Optional[str] = None

    account_last_four: Optional[str] = None

    transaction_reference: Optional[str] = None

    bank_name: Optional[str] = None
    upi_paid_by: Optional[int] = None

    payment_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# EXPENSE PAID


class ExpensePaid(BaseModel):

    paid_by: int

    payment_method_id: int

    cheque_number: Optional[str] = None

    account_last_four: Optional[str] = None

    transaction_reference: Optional[str] = None

    bank_name: Optional[str] = None

    payment_date: Optional[datetime] = None

    remarks: Optional[str] = None

class ExpenseStatusUpdate(BaseModel):

    status: Literal[
        "Approved",
        "Rejected",
        "Paid"
    ]

    approved_by: Optional[int] = None
    paid_by: Optional[int] = None

    remarks: Optional[str] = None

    payment_method_id: Optional[int] = None
    cheque_number: Optional[str] = None
    account_last_four: Optional[str] = None
    transaction_reference: Optional[str] = None
    bank_name: Optional[str] = None
    payment_date: Optional[datetime] = None


# DASHBOARD


class DashboardResponse(BaseModel):

    total_expenses: int

    pending: int

    approved: int

    rejected: int

    paid: int

    total_amount: Decimal = Decimal("0")

    model_config = ConfigDict(from_attributes=True)


# REPORT


class ReportResponse(BaseModel):

    category_name: str

    total_amount: Decimal

    model_config = ConfigDict(from_attributes=True)



# EXPENSE PAYMENT DETAIL (drill-down by payment method)


class ExpensePaymentDetailResponse(BaseModel):

    payment_id: int

    expense_id: int

    expense_number: str

    title: str

    expense_date: date

    amount: Decimal

    status: str

    created_by: int

    payment_method_id: int

    payment_method_name: str

    cheque_number: Optional[str] = None

    account_last_four: Optional[str] = None

    transaction_reference: Optional[str] = None

    bank_name: Optional[str] = None

    payment_date: Optional[datetime] = None

    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# EXPENSE PAYMENT UPDATE (correct/add cheque & other details)


class ExpensePaymentUpdate(BaseModel):

    cheque_number: Optional[str] = None

    account_last_four: Optional[str] = None

    transaction_reference: Optional[str] = None

    bank_name: Optional[str] = None

    payment_date: Optional[datetime] = None

class PaymentMethodReportResponse(BaseModel):
    payment_method_id: int
    payment_method_name: str
    payment_count: int
    total_amount: Decimal



# PAYMENT PERIOD REPORT


class PaymentPeriodReportResponse(BaseModel):
    payment_method_id:int
    payment_method_name:str
    payment_count:int
    total_amount:Decimal

    model_config = ConfigDict(from_attributes=True)


# PAYMENT PERIOD DETAIL


class PaymentPeriodDetailResponse(BaseModel):
    payment_id:int
    expense_id:int

    expense_number:str
    title:str
    expense_date:date
    amount:Decimal
    status: str
    created_by: int

    payment_method_id: int
    payment_method_name: str

    cheque_number: Optional[str] = None
    account_last_four: Optional[str] = None
    transaction_reference: Optional[str] = None
    bank_name: Optional[str] = None

    payment_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)





# SUB-VENDOR CATEGORY REQUEST


class CategoryRequestCreate(BaseModel):

    category_name: str

    requested_by: int

    remarks: Optional[str] = None

class CategoryRequestResponse(BaseModel):

    id: int

    category_name: str

    requested_by: int

    status: str

    remarks: Optional[str] = None

    approved_by: Optional[int] = None

    approved_at: Optional[datetime] = None

    rejection_reason: Optional[str] = None

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

    class Config:

        from_attributes = True


# SUB-VENDOR SUB-CATEGORY REQUEST


class SubCategoryRequestCreate(BaseModel):

    category_id: int

    subcategory_name: str

    requested_by: int

    remarks: Optional[str] = None

class SubCategoryRequestResponse(BaseModel):

    id: int

    category_id: int

    subcategory_name: str

    requested_by: int

    status: str

    remarks: Optional[str] = None

    approved_by: Optional[int] = None

    approved_at: Optional[datetime] = None

    rejection_reason: Optional[str] = None

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

    class Config:

        from_attributes = True


# ADMIN CATEGORY REQUEST ACTIONS


class CategoryRequestApproval(BaseModel):
    approved_by: int

class CategoryRequestRejection(BaseModel):
    rejected_by: int
    rejection_reason: str


# ADMIN SUBCATEGORY REQUEST ACTIONS


class SubCategoryRequestApproval(BaseModel):
    approved_by: int

class SubCategoryRequestRejection(BaseModel):
    rejected_by: int
    rejection_reason: str        


# SUB-VENDOR ACTIVITY LOG


class SubVendorActivityResponse(BaseModel):

    id: int

    user_id: int

    action: str

    module: str

    record_id: Optional[int] = None

    description: Optional[str] = None

    status: str

    details: Optional[str] = None

    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True   



# SUB-VENDOR MANAGEMENT


class SubVendorCreate(BaseModel):

    name: str

    email: str

    phone: Optional[str] = None

    password: str

class SubVendorUpdate(BaseModel):

    name: Optional[str] = None

    email: Optional[str] = None

    phone: Optional[str] = None

    password: Optional[str] = None

class SubVendorCreate(BaseModel):

    name: str

    email: str

    phone: Optional[str] = None

    password: str

class SubVendorUpdate(BaseModel):

    name: Optional[str] = None

    email: Optional[str] = None

    phone: Optional[str] = None

    password: Optional[str] = None

class SubVendorStatusUpdate(BaseModel):

    is_active: bool

class SubVendorResponse(BaseModel):

    id: int

    name: str

    email: str

    phone: Optional[str] = None

    is_active: bool

    created_at: datetime

    updated_at: datetime

    class Config:

        from_attributes = True    

class SubVendorResponse(BaseModel):

    id: int

    name: str

    email: str

    phone: Optional[str] = None

    is_active: bool

    created_at: datetime

    updated_at: datetime

    class Config:

        from_attributes = True

class SubVendorLogin(BaseModel):
    email:str
    password:str


class CategoryPeriodReportResponse(BaseModel):

    category_id: int

    category_name: str

    expense_count: int

    total_amount: Decimal

class SubCategoryPeriodReportResponse(BaseModel):

    subcategory_id: int

    category_id: int

    category_name: str

    subcategory_name: str

    expense_count: int

    total_amount: Decimal

class CategorySubCategoryPeriodReportResponse(BaseModel):

    period: str

    start_date: date

    end_date: date

    category_report: list[
        CategoryPeriodReportResponse
    ]

    subcategory_report: list[
        SubCategoryPeriodReportResponse
    ]    


class WalletResponse(BaseModel):
    id:int
    owner_type:str
    owner_id: int
    balance: Decimal
    currency: str
    is_active: bool
    created_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WalletTransactionCreate(BaseModel):
    transaction_type: Literal[
        "CREDIT",
        "DEBIT"
    ]

    amount: Decimal

    performed_by: Optional[int] = None

    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    description: Optional[str] = None


class WalletTransactionResponse(BaseModel):
    id: int
    wallet_id: int
    performed_by: Optional[int] = None
    transaction_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AdminWalletTransactionCreate(BaseModel):
    owner_type: Literal[
        "EMPLOYEE",
        "SUB_VENDOR"
    ]
    owner_id: int
    transaction_type: Literal[
        "CREDIT",
        "DEBIT"
    ]
    amount: Decimal
    performed_by: Optional[int] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    description: Optional[str] = None

class WalletDetailsResponse(BaseModel):
    wallet: WalletResponse
    transactions: list[WalletTransactionResponse]    


# Employee DB Model 

class EmployeeCreate(BaseModel):
    name:str
    email:str
    phone:Optional[str] = None
    password: str


class EmployeeResponse(BaseModel):
    id:int
    sub_vendor_id: int
    name:str
    email:str
    phone:Optional[str] = None
    is_active:bool
    created_at:datetime
    updated_at:datetime

    class Config:
        from_attributes = True


class EmployeeStatusUpdate(BaseModel):
    is_active:bool

class EmployeeLogin(BaseModel):
    email: str
    password: str


class AdminRegister(BaseModel):
    Name:str
    email_id:str
    phone_number:str
    password:str

class AdminLogin(BaseModel):
    email_id:str
    password:str    

class AdminForgotPassword(BaseModel):
    email_id:str 

class AdminResetPassword(BaseModel):
    token:str
    new_password:str








