from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Literal, Optional
from datetime import datetime
from app.database import get_db
from app.models import FinancialRecord, RecordType, User
from app.schemas import DashboardSummary, CategoryTotal, TrendEntry, RecordResponse
from app.dependencies import require_any_role

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


def _base_query(db: Session, date_from: Optional[datetime], date_to: Optional[datetime]):
    q = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)
    if date_from:
        q = q.filter(FinancialRecord.date >= date_from)
    if date_to:
        q = q.filter(FinancialRecord.date <= date_to)
    return q


@router.get("/summary", response_model=DashboardSummary, summary="High-level financial summary [All Roles]")
def get_summary(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    """Returns total income, expenses, net balance, and record counts — optionally scoped to a date range."""
    q = _base_query(db, date_from, date_to)
    rows = (
        q.with_entities(
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        )
        .group_by(FinancialRecord.type)
        .all()
    )
    totals = {r.type: (r.total or 0.0, r.count) for r in rows}
    income, income_count = totals.get(RecordType.income, (0.0, 0))
    expense, expense_count = totals.get(RecordType.expense, (0.0, 0))
    return DashboardSummary(
        total_income=round(income, 2),
        total_expense=round(expense, 2),
        net_balance=round(income - expense, 2),
        total_records=income_count + expense_count,
        income_records=income_count,
        expense_records=expense_count,
    )


@router.get("/categories", response_model=List[CategoryTotal], summary="Category-wise totals [All Roles]")
def get_category_totals(
    type: Optional[RecordType] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    """Returns sum and count of records grouped by category and type, ordered by total descending."""
    q = _base_query(db, date_from, date_to)
    if type:
        q = q.filter(FinancialRecord.type == type)
    rows = (
        q.with_entities(
            FinancialRecord.category,
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        )
        .group_by(FinancialRecord.category, FinancialRecord.type)
        .order_by(func.sum(FinancialRecord.amount).desc())
        .all()
    )
    return [CategoryTotal(category=r.category, type=r.type, total=round(r.total or 0.0, 2), count=r.count) for r in rows]


@router.get(
    "/trends",
    response_model=List[TrendEntry],
    summary="Income vs expense trends [All Roles]",
)
def get_trends(
    granularity: Literal["monthly", "weekly"] = Query(
        "monthly",
        description="Group results by **monthly** (YYYY-MM) or **weekly** (YYYY-Www) periods",
    ),
    year: Optional[int] = Query(None, description="Scope results to a specific year"),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    """
    Returns income, expense, and net figures grouped by time period.

    - `granularity=monthly` → periods like `2024-03`
    - `granularity=weekly`  → periods like `2024-W12`

    Optionally filter to a single year with the `year` query parameter.
    """
    q = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)
    if year:
        q = q.filter(extract("year", FinancialRecord.date) == year)

    if granularity == "monthly":
        period_col = func.strftime("%Y-%m", FinancialRecord.date).label("period")
    else:
        # ISO week: strftime('%Y-W%W') gives e.g. "2024-W03"
        period_col = func.strftime("%Y-W%W", FinancialRecord.date).label("period")

    rows = (
        q.with_entities(
            period_col,
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
        )
        .group_by("period", FinancialRecord.type)
        .order_by("period")
        .all()
    )

    pivot: dict = {}
    for r in rows:
        if r.period not in pivot:
            pivot[r.period] = {"income": 0.0, "expense": 0.0}
        pivot[r.period][r.type.value] += r.total or 0.0

    return [
        TrendEntry(
            period=period,
            income=round(vals["income"], 2),
            expense=round(vals["expense"], 2),
            net=round(vals["income"] - vals["expense"], 2),
        )
        for period, vals in sorted(pivot.items())
    ]


@router.get("/recent", response_model=List[RecordResponse], summary="Recent financial activity [All Roles]")
def get_recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of recent records (max 50)"),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    """Returns the `limit` most recent records by date. Useful for dashboard activity feeds."""
    return (
        db.query(FinancialRecord)
        .filter(FinancialRecord.is_deleted == False)
        .order_by(FinancialRecord.date.desc())
        .limit(limit)
        .all()
    )
