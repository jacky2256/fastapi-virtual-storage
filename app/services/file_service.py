# app/services/business/file_service.py
import uuid
from pathlib import Path
from typing import Optional, List, BinaryIO
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.db.crud import FileRepository, FolderRepository
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

    async def list(self, folder_id: Optional[UUID] = None) -> List[FileOut]:
        """
        List files under a given folder.
        """
        db_items: List[FileDB] = await self.repo.list_by_folder(folder_id)
        return [FileOut.model_validate(item.model_dump()) for item in db_items]

    async def get_file_info_by_id(self, file_id: UUID) -> FileOut:
        """
        Retrieve a file info by its ID.
        """
        db_item: FileDB = await self.repo.get_by_id(file_id)
        return FileOut.model_validate(db_item.model_dump())

    async def get_file_info_for_download(self, file_id: UUID) -> FileDownloadInfo:
        db_item: FileDB = await self.repo.get_by_id(file_id)
        return FileDownloadInfo.model_validate(db_item.model_dump())

    async def upload(
        self,
        data: FileIn,
        stream: BinaryIO
    ) -> FileOut:
        # 1) Сгенерировать UUID для файла
        file_id = uuid.uuid4()

        # 2) Определить виртуальный путь с этим UUID и расширением
        ext = Path(data.name).suffix  # например, ".png"
        if data.folder_id:
            folder = await self.folder_repo.get_by_id(data.folder_id)
            base_virt = folder.virtual_path.rstrip("/")
        else:
            base_virt = ""
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

        # 5) Создать запись в БД, передав нужные поля
        db_item: FileDB = await self.repo.create(
            data,
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

    async def delete(self, file_id: UUID) -> None:
        """
        Remove file both from disk and database.
        """
        db_item: FileDB = await self.repo.get_by_id(file_id)
        await self.disk.delete_file(Path(db_item.storage_path))
        await self.repo.delete(file_id)
