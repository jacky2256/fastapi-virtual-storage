# app/services/business/file_service.py
import uuid
from pathlib import Path
from typing import Optional, List, BinaryIO
from uuid import UUID

from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.db.crud import FileRepository, FolderRepository
from app.schemas import PaginationParamsSchema
from app.services import FileDiskService
from app.schemas.file import FileIn, FileUpdate, FileDB, FileOut, FileDownloadInfo


class FileService:
    """
    Business‐logic service that coordinates file operations both
    on the filesystem (via FileDiskService) and in the database
    (via FileRepository).

    Returns FileOut for all operations.
    """

    def __init__(
        self,
        session: AsyncSession,
        repo: FileRepository,
        folder_repo: FolderRepository,
        disk: FileDiskService,
    ):
        self.session = session
        self.repo = repo
        self.folder_repo = folder_repo
        self.disk = disk

    async def list_files_by_folder_path(
            self,
            path: str,
            params: PaginationParamsSchema,
    ) -> Page[FileOut]:
        """
        List files under a given folder.
        """
        folder = await self.folder_repo.get_by_virtual_path(path)
        return await self.repo.list_by_folder_path(folder.id, params)

    async def get_file_info_by_id(self, file_id: UUID) -> FileOut:
        """
        Retrieve a file info by its ID.
        """
        db_item: FileDB = await self.repo.get_by_id(file_id)
        return FileOut.model_validate(db_item.model_dump())

    async def get_file_info_for_download(self, file_path: str) -> FileDownloadInfo:
        db_item: FileDB = await self.repo.get_by_path(file_path)
        return FileDownloadInfo.model_validate(db_item.model_dump())

    async def upload(
        self,
        file_name: Optional[str],
        uploader_user_id: uuid.UUID,
        folder_path: str,
        stream: BinaryIO
    ) -> FileOut:
        folder_info = await self.folder_repo.get_by_virtual_path(folder_path)

        # 1) Сгенерировать UUID для файла
        file_id = uuid.uuid4()
        f_name = str(file_id) if file_name is None else file_name

        # 2) Определить виртуальный путь с этим UUID и расширением
        ext = Path(f_name).suffix  # например, ".png"
        base_virt = folder_info.virtual_path.rstrip("/")
        virt_file_path = f"{base_virt}/{file_id}{ext}"

        # 3) Сохранить на диск в папку base_virt
        phys_path = await self.disk.save_file(
            stream,
            base_virt or "/",      # виртуальная папка, в которой лежит файл
            f"{file_id}{ext}"      # имя файла на диске — тоже UUID.ext
        )

        # 4) Определить размер и MIME
        size_bytes = phys_path.stat().st_size
        mime_type = await self.disk.get_mime_type(phys_path)

        file_info = FileIn(
            name=f_name,
            uploader_user_id=uploader_user_id,
            folder_id=folder_info.id,
        )
        # 5) Создать запись в БД, передав нужные поля
        db_item: FileDB = await self.repo.create(
            file_info,
            storage_path=str(phys_path),
            virtual_path=virt_file_path,
            size_bytes=size_bytes,
            mime_type=mime_type,
            file_id=file_id,
        )

        return FileOut.model_validate(db_item.model_dump())

    async def update_metadata(
        self,
        file_id: UUID,
        data: FileUpdate
    ) -> FileOut:
        """
        Update file metadata (name, virtual_path, folder_id).
        """
        db_item = await self.repo.get_by_id(file_id)

        # If renaming or moving on disk is needed:
        old_path = Path(db_item.storage_path)
        new_path = self.disk.compute_file_path(
            data.virtual_path or db_item.virtual_path,
            data.name or db_item.name
        )
        if str(old_path) != str(new_path):
            await self.disk.delete_file(new_path)  # remove existing if any
            await self.disk.save_file(old_path.open("rb"),
                                      data.virtual_path or db_item.virtual_path,
                                      data.name or db_item.name)
            await self.disk.delete_file(old_path)

        updated_db: FileDB = await self.repo.update(
            file_id,
            data,
            storage_path=str(new_path)
        )
        return FileOut.model_validate(updated_db.model_dump())

    async def delete_file_by_id(self, file_id: UUID) -> None:
        """
        Remove file both from disk and database.
        """
        db_item: FileDB = await self.repo.get_by_id(file_id)
        await self.disk.delete_file(Path(db_item.storage_path))
        await self.repo.delete(file_id)

    async def delete_file_by_path(self, path: str) -> None:
        """
        Remove file both from disk and database.
        """
        db_item: FileDB = await self.repo.get_by_path(path)
        await self.disk.delete_file(Path(db_item.storage_path))
        await self.repo.delete(db_item.id)
