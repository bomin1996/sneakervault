import secrets

from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://sneakervault:password@localhost:3306/sneakervault"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: str = ""
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_secure(cls, v: str) -> str:
        insecure_defaults = {"dev-secret-key-change-in-production", "secret", "changeme", ""}
        if v in insecure_defaults:
            raise ValueError("SECRET_KEY is insecure. Set a strong key in .env file.")
        return v

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
