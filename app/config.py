import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI AWS Cloud Application"
    APP_ENV: str = "production"
    DEBUG: bool = False
    PORT: int = 8000

    DB_HOST: Optional[str] = None
    DB_PORT: int = 5432
    DB_USER: Optional[str] = "postgres"
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = "fastapiprod"
    DATABASE_URL: Optional[str] = None

    AWS_REGION: str = "ap-southeast-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    S3_FOLDER: str = "uploads/"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url

        if self.DB_HOST and self.DB_USER and self.DB_PASSWORD and self.DB_NAME:
            return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

        return "sqlite:///./local_test.db"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
