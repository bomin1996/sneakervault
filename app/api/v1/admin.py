from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.partner import Partner
from app.models.product import Product
from app.schemas.partner import PartnerResponse, PartnerAdminUpdate
from app.schemas.product import ProductResponse, ProductListResponse

router = APIRouter()


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
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(partner, field, value)
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
        "approved_partners": db.query(Partner).filter(Partner.status == "approved").count(),
        "pending_partners": db.query(Partner).filter(Partner.status == "pending").count(),
        "total_products": db.query(Product).count(),
        "active_products": db.query(Product).filter(Product.is_active == True).count(),
    }
