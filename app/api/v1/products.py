from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_partner
from app.models.partner import Partner
from app.models.product import Product
from app.models.price_history import PriceHistory, PriceSource
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
)

router = APIRouter()


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    product = Product(partner_id=partner.id, **body.model_dump())
    db.add(product)
    db.flush()

    # Record initial price history
    history = PriceHistory(
        product_id=product.id,
        price=product.current_price,
        source=PriceSource.PARTNER,
    )
    db.add(history)
    db.commit()
    db.refresh(product)
    return product


@router.get("", response_model=ProductListResponse)
def list_products(
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    brand_id: int | None = None,
    category_id: int | None = None,
    search: str | None = None,
):
    query = db.query(Product).filter(Product.partner_id == partner.id)

    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()

    return ProductListResponse(items=items, total=total, page=page, size=size)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id, Product.partner_id == partner.id
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    body: ProductUpdate,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id, Product.partner_id == partner.id
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    update_data = body.model_dump(exclude_unset=True)

    # Record price change
    if "current_price" in update_data and update_data["current_price"] != product.current_price:
        history = PriceHistory(
            product_id=product.id,
            price=update_data["current_price"],
            previous_price=product.current_price,
            source=PriceSource.PARTNER,
        )
        db.add(history)

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id, Product.partner_id == partner.id
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product.is_active = False
    db.commit()
