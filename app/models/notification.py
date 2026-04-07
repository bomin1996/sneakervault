from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NotificationType(str, PyEnum):
    PRICE_DROP = "price_drop"
    PRICE_SURGE = "price_surge"
    STOCK_LOW = "stock_low"
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id"), index=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    partner: Mapped["Partner"] = relationship(back_populates="notifications")


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id"), index=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    threshold_percent: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    partner: Mapped["Partner"] = relationship(back_populates="notification_settings")
