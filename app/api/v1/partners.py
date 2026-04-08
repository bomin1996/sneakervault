from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, get_current_partner
from app.models.user import User
from app.models.partner import Partner
from app.schemas.partner import PartnerCreate, PartnerUpdate, PartnerResponse, PartnerWithKeyResponse
from app.utils.security import generate_api_key

router = APIRouter()


@router.post("/register", response_model=PartnerWithKeyResponse, status_code=status.HTTP_201_CREATED)
def register_partner(
    body: PartnerCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.query(Partner).filter(Partner.user_id == user.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already registered as partner")
    if db.query(Partner).filter(Partner.business_number == body.business_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Business number already exists")

    partner = Partner(
        user_id=user.id,
        business_name=body.business_name,
        business_number=body.business_number,
        contact_phone=body.contact_phone,
        api_key=generate_api_key(),
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


@router.get("/me", response_model=PartnerResponse)
def get_my_partner(partner: Partner = Depends(get_current_partner)):
    return PartnerResponse.from_partner(partner)


@router.patch("/me", response_model=PartnerResponse)
def update_my_partner(
    body: PartnerUpdate,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(partner, field, value)
    db.commit()
    db.refresh(partner)
    return PartnerResponse.from_partner(partner)


@router.post("/me/regenerate-key", response_model=PartnerWithKeyResponse)
def regenerate_api_key(
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    partner.api_key = generate_api_key()
    db.commit()
    db.refresh(partner)
    return partner
