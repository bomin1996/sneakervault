from datetime import datetime
from pydantic import BaseModel

from app.models.product import ProductCondition


class ProductCreate(BaseModel):
    brand_id: int
    category_id: int
    model_number: str
    name: str
    description: str | None = None
    size: str
    condition: ProductCondition = ProductCondition.NEW
    release_price: int
    current_price: int
    stock_quantity: int = 0
    image_url: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    current_price: int | None = None
    stock_quantity: int | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: int
    partner_id: int
    brand_id: int
    category_id: int
    model_number: str
    name: str
    description: str | None
    size: str
    condition: ProductCondition
    release_price: int
    current_price: int
    stock_quantity: int
    image_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    size: int


class BrandResponse(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: str | None

    model_config = {"from_attributes": True}


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}
