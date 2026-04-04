from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models import FinancialRecord, RecordType, User, UserRole
from app.schemas import RecordCreate, RecordUpdate, RecordResponse, PaginatedRecords
from app.dependencies import require_admin, require_analyst_or_admin, require_any_role

router = APIRouter(prefix="/records", tags=["Financial Records"])

PAGE_SIZE_MAX = 100


def _get_record_or_404(record_id: int, db: Session) -> FinancialRecord:
    record = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.id == record_id, FinancialRecord.is_deleted == False)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found")
    return record


@router.post(
    "/",
    response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a financial record [Admin]",
)
def create_record(
    payload: RecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    **Admin only.** Creates a new financial record (income or expense).
    """
    record = FinancialRecord(
        amount=payload.amount,
        type=payload.type,
        category=payload.category,
        date=payload.date,
        notes=payload.notes,
        created_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get(
    "/",
    response_model=PaginatedRecords,
    summary="List financial records [All Roles]",
)
def list_records(
    type: Optional[RecordType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category (case-insensitive)"),
    date_from: Optional[datetime] = Query(None, description="Filter records on or after this date"),
    date_to: Optional[datetime] = Query(None, description="Filter records on or before this date"),
    search: Optional[str] = Query(None, description="Search in notes or category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=PAGE_SIZE_MAX, description="Records per page (max 100)"),
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    """
    Returns a paginated list of financial records. All roles may access this endpoint.

    **Filters available:** `type`, `category`, `date_from`, `date_to`, `search`
    """
    q = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)

    if type is not None:
        q = q.filter(FinancialRecord.type == type)
    if category:
        q = q.filter(FinancialRecord.category.ilike(f"%{category}%"))
    if date_from:
        q = q.filter(FinancialRecord.date >= date_from)
    if date_to:
        q = q.filter(FinancialRecord.date <= date_to)
    if search:
        term = f"%{search}%"
        q = q.filter(
            (FinancialRecord.notes.ilike(term)) | (FinancialRecord.category.ilike(term))
        )

    total = q.count()
    total_pages = max(1, -(-total // page_size))  # ceiling division
    offset = (page - 1) * page_size
    records = q.order_by(FinancialRecord.date.desc()).offset(offset).limit(page_size).all()

    return PaginatedRecords(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        data=records,
    )


@router.get(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Get a single record [All Roles]",
)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_any_role),
):
    """Returns a single financial record by ID. All roles may access this."""
    return _get_record_or_404(record_id, db)


@router.put(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Update a financial record [Admin]",
)
def update_record(
    record_id: int,
    payload: RecordUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    **Admin only.** Partially updates any field of an existing record.
    Only provided fields are updated; omitted fields remain unchanged.
    """
    record = _get_record_or_404(record_id, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft-delete a financial record [Admin]",
)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    **Admin only.** Soft-deletes a record by setting `is_deleted = True`.
    The record is retained in the database for audit purposes but will no
    longer appear in any list or summary endpoints.
    """
    record = _get_record_or_404(record_id, db)
    record.is_deleted = True
    db.commit()
    return {"message": f"Record {record_id} has been deleted", "id": record_id}
