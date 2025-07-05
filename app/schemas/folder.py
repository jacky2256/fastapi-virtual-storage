from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.utils.validators import NoSlashString


class FolderIn(BaseModel):
    name: NoSlashString
    parent_id: Optional[UUID] = Field(..., description="ID родительской папки")
    creator_user_id: UUID = Field(..., description="ID пользователя, создавшего папку")
    is_published: bool = Field(default=True, description="Могут ли видеть его не зарегистрированные пользователи")


class FolderOut(FolderIn):
    id: UUID = Field(..., description="ID папки")
    virtual_path: str = Field(..., description="Виртуальный путь к папке на сайте")
    created_at: datetime = Field(..., description="Дата создания папки")
    updated_at: datetime = Field(..., description="Дата обновления папки")


class FolderUpdate(BaseModel):
    name: Optional[NoSlashString] = Field(default=None)
    parent_id: Optional[UUID] = Field(default=None, description="ID родительской папки")
    creator_user_id: Optional[UUID] = Field(default=None, description="ID пользователя, создавшего папку")
    is_published: Optional[bool] = Field(default=None, description="Могут ли видеть его не зарегистрированные пользователи")


class FolderDB(BaseModel):
    id: UUID = Field(..., description="ID папки")
    name: str = Field(..., description="Название папки")
    storage_path: str = Field(..., description="Реальная часть пути к папке на диске")
    virtual_path: str = Field(..., description="Виртуальный путь к папке на сайте")
    creator_user_id: UUID = Field(..., description="ID пользователя, создавшего папку")
    parent_id: Optional[UUID] = Field(..., description="ID родительской папки")
    is_published: bool = Field(default=True, description="Могут ли видеть его не зарегистрированные пользователи")
    access_url: Optional[str] = Field(..., description="URL для доступа к папке")
    created_at: datetime = Field(..., description="Дата создания папки")
    updated_at: datetime = Field(..., description="Дата обновления папки")

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )
