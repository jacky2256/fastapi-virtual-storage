# app/schemas/file.py

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.utils.validators import NoSlashString

class FileDownloadInfo(BaseModel):
    name: str
    storage_path: str
    mime_type: str


class FileIn(BaseModel):
    """
    DTO for creating a new File.
    """
    name: NoSlashString = Field(..., description="Original filename (3–100 chars, no '/')")
    uploader_user_id: UUID = Field(..., description="UUID of the user uploading the file")
    folder_id: Optional[UUID] = Field(None, description="UUID of the parent folder (optional)")


class FileOut(FileIn):
    """
    DTO returned to clients for a File resource.
    """
    id: UUID = Field(..., description="UUID of the file")
    size_bytes: int = Field(..., description="Size of the file in bytes")
    mime_type: str = Field(..., description="MIME type, e.g. 'image/jpeg'")
    virtual_path: str = Field(..., description="New virtual path (optional)")
    access_url: Optional[str] = Field(None, description="Public URL to download or view the file")
    created_at: datetime = Field(..., description="Timestamp when created")
    updated_at: datetime = Field(..., description="Timestamp when last updated")


class FileUpdate(BaseModel):
    """
    DTO for updating File metadata.
    """
    name: Optional[NoSlashString] = Field(None, description="New filename (optional)")
    folder_id: Optional[UUID] = Field(None,description="New parent folder UUID (optional)")


class FileDB(BaseModel):
    """
    Internal Pydantic model for File ORM instances.
    """
    id: UUID = Field(..., description="UUID of the file")
    name: str = Field(..., description="Original filename")
    storage_path: str = Field(..., description="Physical path on disk")
    virtual_path: str = Field(..., description="Virtual path on website")
    uploader_user_id: UUID = Field(..., description="Uploader's UUID")
    folder_id: Optional[UUID] = Field(None, description="Parent folder UUID")
    size_bytes: int = Field(..., description="Size in bytes")
    mime_type: str = Field(..., description="MIME type")
    access_url: Optional[str] = Field(None, description="Public access URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")

    model_config = ConfigDict(
        from_attributes=True
    )
