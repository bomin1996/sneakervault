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
    api_key_last4: str | None = None
    api_call_limit: int
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_partner(cls, partner, show_full_key: bool = False):
        data = {
            "id": partner.id,
            "business_name": partner.business_name,
            "business_number": partner.business_number,
            "contact_phone": partner.contact_phone,
            "status": partner.status,
            "tier": partner.tier,
            "api_key_last4": partner.api_key[-4:] if partner.api_key else None,
            "api_call_limit": partner.api_call_limit,
            "created_at": partner.created_at,
        }
        if show_full_key:
            data["api_key_last4"] = partner.api_key
        return cls(**data)


class PartnerWithKeyResponse(PartnerResponse):
    api_key: str

    model_config = {"from_attributes": True}


class PartnerAdminUpdate(BaseModel):
    status: PartnerStatus | None = None
    tier: PartnerTier | None = None
    api_call_limit: int | None = None
