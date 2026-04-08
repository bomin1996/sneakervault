from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.api.deps import get_current_partner
from app.models.partner import Partner
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.schemas.price import PriceHistoryResponse, PriceTrendResponse, AIAnalysisResponse
from app.services.ai_service import analyze_price_trend

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

TREND_HISTORY_LIMIT = 50
AI_ANALYSIS_HISTORY_LIMIT = 30


@router.get("/{product_id}/history", response_model=list[PriceHistoryResponse])
def get_price_history(
    product_id: int,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    product = db.query(Product).filter(
        Product.id == product_id, Product.partner_id == partner.id
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    histories = (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return histories


@router.get("/{product_id}/trend", response_model=PriceTrendResponse)
def get_price_trend(
    product_id: int,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id, Product.partner_id == partner.id
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    stats = db.query(
        func.min(PriceHistory.price),
        func.max(PriceHistory.price),
        func.avg(PriceHistory.price),
    ).filter(PriceHistory.product_id == product_id).first()

    histories = (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.recorded_at.desc())
        .limit(TREND_HISTORY_LIMIT)
        .all()
    )

    min_price, max_price, avg_price = stats
    price_change_rate = 0.0
    if len(histories) >= 2:
        oldest = histories[-1].price
        if oldest > 0:
            price_change_rate = round((product.current_price - oldest) / oldest * 100, 2)

    return PriceTrendResponse(
        product_id=product.id,
        product_name=product.name,
        current_price=product.current_price,
        min_price=min_price or 0,
        max_price=max_price or 0,
        avg_price=round(avg_price or 0, 2),
        price_change_rate=price_change_rate,
        history=histories,
    )


@router.get("/{product_id}/ai-analysis", response_model=AIAnalysisResponse)
@limiter.limit("10/minute")
async def get_ai_analysis(
    request: Request,
    product_id: int,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id, Product.partner_id == partner.id
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    histories = (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.recorded_at.desc())
        .limit(AI_ANALYSIS_HISTORY_LIMIT)
        .all()
    )

    result = await analyze_price_trend(product, histories)
    return result
