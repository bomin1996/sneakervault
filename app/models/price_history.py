from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Integer, DateTime, ForeignKey, Enum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PriceSource(str, PyEnum):
    PARTNER = "partner"
    CRAWL = "crawl"
    MANUAL = "manual"


class PriceHistory(Base):
    __tablename__ = "price_histories"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    price: Mapped[int] = mapped_column(Integer)
    previous_price: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[PriceSource] = mapped_column(Enum(PriceSource), default=PriceSource.PARTNER)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    product: Mapped["Product"] = relationship(back_populates="price_histories")
