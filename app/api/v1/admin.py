import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.partner import Partner, PartnerStatus
from app.models.product import Product
from app.models.audit_log import AuditLog
from app.schemas.partner import PartnerResponse, PartnerAdminUpdate
from app.schemas.product import ProductResponse, ProductListResponse

router = APIRouter()


def _create_audit_log(
    db: Session, admin_id: int, action: str,
    target_type: str, target_id: int, details: dict | None = None,
) -> None:
    log = AuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details, ensure_ascii=False) if details else None,
    )
    db.add(log)


@router.get("/partners", response_model=list[PartnerResponse])
def list_all_partners(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    status_filter: str | None = None,
):
    query = db.query(Partner)
    if status_filter:
        query = query.filter(Partner.status == status_filter)
    return query.all()


@router.get("/partners/{partner_id}", response_model=PartnerResponse)
def get_partner(
    partner_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    return partner


@router.patch("/partners/{partner_id}", response_model=PartnerResponse)
def update_partner(
    partner_id: int,
    body: PartnerAdminUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")

    changes = body.model_dump(exclude_unset=True)
    old_values = {field: getattr(partner, field).value if hasattr(getattr(partner, field), 'value') else getattr(partner, field) for field in changes}

    for field, value in changes.items():
        setattr(partner, field, value)

    _create_audit_log(
        db, admin_id=admin.id, action="update_partner",
        target_type="partner", target_id=partner_id,
        details={"old": old_values, "new": {k: v.value if hasattr(v, 'value') else v for k, v in changes.items()}},
    )

    db.commit()
    db.refresh(partner)
    return partner


@router.get("/products", response_model=ProductListResponse)
def list_all_products(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    partner_id: int | None = None,
):
    query = db.query(Product)
    if partner_id:
        query = query.filter(Product.partner_id == partner_id)

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return ProductListResponse(items=items, total=total, page=page, size=size)


@router.get("/stats")
def get_dashboard_stats(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return {
        "total_partners": db.query(Partner).count(),
        "approved_partners": db.query(Partner).filter(Partner.status == PartnerStatus.APPROVED).count(),
        "pending_partners": db.query(Partner).filter(Partner.status == PartnerStatus.PENDING).count(),
        "total_products": db.query(Product).count(),
        "active_products": db.query(Product).filter(Product.is_active == True).count(),
    }
