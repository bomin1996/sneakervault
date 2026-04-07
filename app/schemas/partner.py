from datetime import datetime
from pydantic import BaseModel

from app.models.partner import PartnerStatus, PartnerTier


class PartnerCreate(BaseModel):
    business_name: str
    business_number: str
    contact_phone: str


class PartnerUpdate(BaseModel):
    business_name: str | None = None
    contact_phone: str | None = None


class PartnerResponse(BaseModel):
    id: int
    business_name: str
    business_number: str
    contact_phone: str
    status: PartnerStatus
    tier: PartnerTier
    api_key: str
    api_call_limit: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PartnerAdminUpdate(BaseModel):
    status: PartnerStatus | None = None
    tier: PartnerTier | None = None
    api_call_limit: int | None = None
