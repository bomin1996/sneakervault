from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PartnerStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class PartnerTier(str, PyEnum):
    BASIC = "basic"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    business_name: Mapped[str] = mapped_column(String(200))
    business_number: Mapped[str] = mapped_column(String(20), unique=True)
    contact_phone: Mapped[str] = mapped_column(String(20))
    status: Mapped[PartnerStatus] = mapped_column(Enum(PartnerStatus, native_enum=False), default=PartnerStatus.PENDING)
    tier: Mapped[PartnerTier] = mapped_column(Enum(PartnerTier, native_enum=False), default=PartnerTier.BASIC)
    api_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    api_call_limit: Mapped[int] = mapped_column(Integer, default=1000)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="partner")
    products: Mapped[list["Product"]] = relationship(back_populates="partner")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="partner")
    notification_settings: Mapped[list["NotificationSetting"]] = relationship(back_populates="partner")
