import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import DateTime, func, ForeignKey, String, BigInteger, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY

class Base(DeclarativeBase):
    pass


class Folder(Base):
    __tablename__ = 'fjc_folder'

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False, doc="Название папки")
    storage_path: Mapped[str] = mapped_column(String, unique=True, nullable=False, doc="Реальная часть пути к папке на диске")
    virtual_path: Mapped[str] = mapped_column(String, unique=True, nullable=False, doc="Виртуальная часть пути на сайте")
    creator_user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("fjc_folder.id", ondelete="CASCADE"), nullable=True, doc="ID родительской папки")
    access_url: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="URL для доступа к папке")
    is_published: Mapped[bool] = mapped_column(default=True, nullable=False, doc="Могут ли видеть его не зарегистрированные пользователи")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now())

    # Relationships
    parent: Mapped[Optional["Folder"]] = relationship("Folder", remote_side="Folder.id", back_populates="children", passive_deletes=True)
    children: Mapped[List["Folder"]] = relationship("Folder", back_populates="parent", cascade="all, delete-orphan", passive_deletes=True)
    files: Mapped[List["File"]] = relationship("File", back_populates="folder", cascade="all, delete-orphan", passive_deletes=True)
    archives: Mapped[List["ResourceArchive"]] = relationship("ResourceArchive", back_populates="folder", cascade="all, delete-orphan", passive_deletes=True)


class File(Base):
    __tablename__ = 'fjc_file'

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False, doc="Название файла")
    storage_path: Mapped[str] = mapped_column(String, unique=True, nullable=False, doc="Реальная часть пути к файлу на диске")
    virtual_path: Mapped[str] = mapped_column(String, unique=True, nullable=False, doc="Виртуальный путь к файлу на сайте")
    uploader_user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, doc="Размер файла в байтах")
    mime_type: Mapped[str] = mapped_column(String, nullable=False, doc="Тип файла 'image/jpeg', 'application/pdf', 'video/mp4'")
    folder_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("fjc_folder.id", ondelete="CASCADE"), nullable=True, doc="ID родительской папки")
    access_url: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="URL для доступа к файлу")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now())

    # Relationships
    folder: Mapped[Optional[Folder]] = relationship("Folder", back_populates="files")


class ResourceArchive(Base):
    __tablename__ = 'fjc_resource_archive'

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    archive_path: Mapped[str] = mapped_column(String, nullable=False, doc="Относительный путь к архиву на диске")
    size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, doc="Размер архива в байтах")
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, doc="Количество файлов в архиве")
    folder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fjc_folder.id", ondelete="CASCADE"), nullable=False, doc="ID папки, которая была заархивирована")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now())

    # Relationships
    folder: Mapped[Folder] = relationship("Folder", back_populates="archives")