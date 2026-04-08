import secrets
from datetime import datetime, timedelta, timezone

import redis
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_settings = get_settings()
_redis_client = redis.from_url(_settings.REDIS_URL, decode_responses=True)

REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, is_admin: bool = False) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "is_admin": is_admin, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(user_id: int) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh", "jti": secrets.token_hex(16)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise ValueError("Token has expired")
    except JWTError:
        raise ValueError("Invalid token")

    if _is_token_blacklisted(token):
        raise ValueError("Token has been revoked")

    return payload


def blacklist_token(token: str) -> None:
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        exp = payload.get("exp", 0)
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 0)
        if ttl > 0:
            _redis_client.setex(f"token_blacklist:{token}", ttl, "1")
    except JWTError:
        pass


def _is_token_blacklisted(token: str) -> bool:
    return _redis_client.exists(f"token_blacklist:{token}") > 0


def generate_api_key() -> str:
    return secrets.token_hex(32)
