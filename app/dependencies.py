# app/api/dependencies.py

from pathlib import Path

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.crud import FileRepository
from app.db.session import get_db_session
from app.db.crud.folder import FolderRepository
from app.services import FileService, FileDiskService
from app.services.folder_disc_service import FolderDiskService
from app.services.folder_service import FolderService


def get_folder_service(
    session: AsyncSession = Depends(get_db_session),
) -> FolderService:
    """
    FastAPI dependency that provides a FolderService instance,
    сконфигурированный с сессией, репозиторием и дисковым сервисом.
    """
    repo = FolderRepository(session)
    disk = FolderDiskService(base_path=Path(settings.STORAGE_BASE_PATH))
    return FolderService(
        session=session,
        repo=repo,
        disk=disk,
        base_virtual=settings.VIRTUAL_BASE_PATH
    )

def get_file_service(
    session: AsyncSession = Depends(get_db_session),
) -> FileService:
    """
    FastAPI dependency that provides a FileService instance,
    configured with the AsyncSession, FileRepository, and FileDiskService.
    """
    repo = FileRepository(session)
    folder_repo = FolderRepository(session)
    disk = FileDiskService(
        base_path=Path(settings.STORAGE_BASE_PATH),
        allowed_extensions=getattr(settings, "ALLOWED_FILE_EXTENSIONS", None),
    )
    return FileService(
        session=session,
        repo=repo,
        folder_repo=folder_repo,
        disk=disk,
    )
