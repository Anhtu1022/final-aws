from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.schemas import HealthResponse
from app.services.s3_service import s3_service

router = APIRouter(tags=["Health & Status"])
settings = get_settings()


@router.get("/", summary="Root Welcome Endpoint")
def read_root():
    return {
        "message": "Welcome to FastAPI on AWS Cloud!",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health"
    }


@router.get("/health", response_model=HealthResponse, summary="System Health & Cloud Connectivity")
def health_check(db: Session = Depends(get_db)):
    """
    Checks the status of the API, RDS Database connection, and S3 configuration.
    """
    # 1. Test Database connection
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    # 2. Test S3 Bucket accessibility
    s3_connected = s3_service.check_bucket_access()

    db_type = "PostgreSQL (AWS RDS)" if "postgresql" in settings.get_database_url() else "SQLite (Local)"

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        database_connected=db_connected,
        database_type=db_type,
        s3_configured=s3_connected,
        s3_bucket=settings.S3_BUCKET_NAME,
        timestamp=datetime.now(timezone.utc)
    )
