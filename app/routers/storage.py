from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FileUpload
from app.schemas import FileUploadResponse, PresignedUrlResponse
from app.services.s3_service import s3_service

router = APIRouter(prefix="/files", tags=["File Storage (AWS S3)"])


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED, summary="Upload File to S3")
def upload_file_to_s3(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Task 3.2 & 3.3: Uploads a file directly to AWS S3, then saves its metadata into RDS PostgreSQL.
    """
    # 1. Upload to S3
    upload_result = s3_service.upload_file(file)

    # 2. Save metadata to Database
    db_file = FileUpload(
        original_filename=file.filename,
        s3_key=upload_result["s3_key"],
        s3_url=upload_result["s3_url"],
        file_size=upload_result["file_size"],
        content_type=upload_result["content_type"]
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return db_file


# Alias for convenience: /upload
@router.post("", include_in_schema=False)
def upload_file_alias(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return upload_file_to_s3(file=file, db=db)


@router.get("/", response_model=List[FileUploadResponse], summary="List Uploaded Files")
def list_files(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(FileUpload).offset(skip).limit(limit).all()


@router.get("/{file_id}/download-url", response_model=PresignedUrlResponse, summary="Get Presigned S3 Download URL")
def get_download_url(file_id: int, expires_in: int = 3600, db: Session = Depends(get_db)):
    db_file = db.query(FileUpload).filter(FileUpload.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File record not found")

    url = s3_service.generate_presigned_url(db_file.s3_key, expiration=expires_in)
    return PresignedUrlResponse(
        s3_key=db_file.s3_key,
        download_url=url,
        expires_in_seconds=expires_in
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete File from S3 and DB")
def delete_file(file_id: int, db: Session = Depends(get_db)):
    db_file = db.query(FileUpload).filter(FileUpload.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File record not found")

    # Delete from S3
    s3_service.delete_file(db_file.s3_key)

    # Delete from DB
    db.delete(db_file)
    db.commit()
    return None
