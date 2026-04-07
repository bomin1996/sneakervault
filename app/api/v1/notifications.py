from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_partner
from app.models.partner import Partner
from app.models.notification import Notification, NotificationSetting
from app.schemas.notification import (
    NotificationResponse, NotificationSettingUpdate, NotificationSettingResponse,
)

router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
    unread_only: bool = False,
    limit: int = Query(20, ge=1, le=100),
):
    query = db.query(Notification).filter(Notification.partner_id == partner.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id, Notification.partner_id == partner.id
    ).first()
    if notification:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
    return notification


@router.post("/read-all")
def mark_all_as_read(
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.partner_id == partner.id, Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


@router.get("/settings", response_model=list[NotificationSettingResponse])
def get_notification_settings(
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    return db.query(NotificationSetting).filter(
        NotificationSetting.partner_id == partner.id
    ).all()


@router.put("/settings", response_model=NotificationSettingResponse)
def update_notification_setting(
    body: NotificationSettingUpdate,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    setting = db.query(NotificationSetting).filter(
        NotificationSetting.partner_id == partner.id,
        NotificationSetting.type == body.type,
    ).first()

    if setting:
        setting.is_enabled = body.is_enabled
        setting.threshold_percent = body.threshold_percent
    else:
        setting = NotificationSetting(
            partner_id=partner.id,
            type=body.type,
            is_enabled=body.is_enabled,
            threshold_percent=body.threshold_percent,
        )
        db.add(setting)

    db.commit()
    db.refresh(setting)
    return setting
