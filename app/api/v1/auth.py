from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import redis

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.utils.security import hash_password, verify_password, create_access_token

router = APIRouter()

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 900  # 15분

settings = get_settings()
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def _login_attempt_key(email: str) -> str:
    return f"login_attempts:{email}"


def _check_login_blocked(email: str) -> None:
    key = _login_attempt_key(email)
    attempts = redis_client.get(key)
    if attempts and int(attempts) >= MAX_LOGIN_ATTEMPTS:
        ttl = redis_client.ttl(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {ttl} seconds.",
        )


def _record_failed_attempt(email: str) -> None:
    key = _login_attempt_key(email)
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, LOGIN_LOCKOUT_SECONDS)
    pipe.execute()


def _clear_login_attempts(email: str) -> None:
    redis_client.delete(_login_attempt_key(email))


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return Token(access_token=create_access_token(user.id, user.is_admin))


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    _check_login_blocked(body.email)

    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        _record_failed_attempt(body.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    _clear_login_attempts(body.email)
    return Token(access_token=create_access_token(user.id, user.is_admin))
