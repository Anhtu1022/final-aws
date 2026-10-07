from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FileUploadResponse(BaseModel):
    id: int
    original_filename: str
    s3_key: str
    s3_url: str
    file_size: int
    content_type: Optional[str]
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class PresignedUrlResponse(BaseModel):
    s3_key: str
    download_url: str
    expires_in_seconds: int


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    database_connected: bool
    database_type: str
    s3_configured: bool
    s3_bucket: Optional[str]
    timestamp: datetime
