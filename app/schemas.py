from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, RecordType


# ─── Auth ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[UserRole] = None


# ─── Users ───────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str
    role: UserRole = UserRole.viewer

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, hyphens, and underscores")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Financial Records ───────────────────────────────────────────────────────

class RecordCreate(BaseModel):
    amount: float
    type: RecordType
    category: str
    date: datetime
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2)

    @field_validator("category")
    @classmethod
    def category_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Category cannot be empty")
        if len(v) > 100:
            raise ValueError("Category must be 100 characters or fewer")
        return v


class RecordUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[RecordType] = None
    category: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2) if v is not None else v


class RecordResponse(BaseModel):
    id: int
    amount: float
    type: RecordType
    category: str
    date: datetime
    notes: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaginatedRecords(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[RecordResponse]


# ─── Dashboard ───────────────────────────────────────────────────────────────

class CategoryTotal(BaseModel):
    category: str
    type: RecordType
    total: float
    count: int

class MonthlyTrend(BaseModel):
    year: int
    month: int
    income: float
    expense: float
    net: float

class DashboardSummary(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float
    total_records: int
    income_records: int
    expense_records: int


class TrendEntry(BaseModel):
    """Unified schema for both monthly and weekly trend data points."""
    period: str    # e.g. "2024-03" (monthly) or "2024-W12" (weekly)
    income: float
    expense: float
    net: float
