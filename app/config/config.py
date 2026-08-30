from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.requests import Request


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    ALEMBIC_DATABASE_URL: str
    JWT_SECRET_KEY: str
    ALGORITHM: str
    REDIS_URL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CACHE_TTL_SECONDS: int = 3600
    CACHE_EXPIRE_SECONDS: int = 60
    LIMIT_OF_REQUESTS: int = 10
    ARTIC_API_URL: str = "https://api.artic.edu/api/v1/artworks"
    SESSION_SECRET_KEY: str

    OPENAI_API_KEY: str
    OPENAI_MODEL: str

    GEMINI_API_KEY: str
    GEMINI_MODEL: str


def get_settings() -> Settings:
    return Settings()


def get_settings_from_lifespan(request: Request) -> Settings:
    return request.app.state.settings