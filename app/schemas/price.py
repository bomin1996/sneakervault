from datetime import datetime
from pydantic import BaseModel

from app.models.price_history import PriceSource


class PriceHistoryResponse(BaseModel):
    id: int
    product_id: int
    price: int
    previous_price: int | None
    source: PriceSource
    ai_summary: str | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class PriceTrendResponse(BaseModel):
    product_id: int
    product_name: str
    current_price: int
    min_price: int
    max_price: int
    avg_price: float
    price_change_rate: float
    history: list[PriceHistoryResponse]


class AIAnalysisResponse(BaseModel):
    product_id: int
    product_name: str
    summary: str
    trend: str
    recommendation: str
