from datetime import datetime
from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    id: int
    type: NotificationType
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationSettingUpdate(BaseModel):
    type: NotificationType
    is_enabled: bool
    threshold_percent: int | None = None


class NotificationSettingResponse(BaseModel):
    id: int
    type: NotificationType
    is_enabled: bool
    threshold_percent: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
