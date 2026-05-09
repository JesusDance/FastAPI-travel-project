import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    TESTING: bool = False
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")


class TestingConfig(Settings):
    TESTING: bool = True
    DATABASE_URL: str = "sqlite:///test.db"