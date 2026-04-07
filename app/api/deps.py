from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.partner import Partner
from app.utils.security import decode_access_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def get_current_partner(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Partner:
    partner = db.query(Partner).filter(Partner.user_id == user.id).first()
    if not partner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Partner registration required")
    if partner.status != "approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Partner status: {partner.status}")
    return partner


def get_partner_by_api_key(
    api_key: str,
    db: Session = Depends(get_db),
) -> Partner:
    partner = db.query(Partner).filter(Partner.api_key == api_key).first()
    if not partner or partner.status != "approved":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return partner
