# app/services/business/folder_service.py

from pathlib import Path
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.db.crud.folder import FolderRepository
from app.services.folder_disc_service import FolderDiskService
from app.schemas.folder import FolderIn, FolderUpdate, FolderDB, FolderOut
from app.utils.exceptions import FolderAlreadyExistsError


class FolderService:
    """
    Business‐logic service that coordinates folder operations both
    on the filesystem (via FolderDiskService) and in the database
    (via FolderRepository).

    Returns FolderOut for all operations.
    """

    def __init__(
        self,
        session: AsyncSession,
        repo: FolderRepository,
        disk: FolderDiskService,
        base_virtual: str = "/"
    ):
        self.session = session
        self.repo = repo
        self.disk = disk
        self.base_virtual = base_virtual.rstrip("/") + "/"

    async def list(self, parent_id: Optional[UUID] = None) -> List[FolderOut]:
        """
        List child folders under a given parent.
        """
        db_items: List[FolderDB] = await self.repo.list_by_parent(parent_id)
        return [FolderOut.model_validate(item) for item in db_items]

    async def get_by_id(self, folder_id: UUID) -> FolderOut:
        """
        Retrieve a folder by its ID, or raise NoResultFound.
        """
        db_item: FolderDB = await self.repo.get_by_id(folder_id)
        return FolderOut.model_validate(db_item.model_dump())

    async def get_by_virtual_path(self, path: str) -> FolderOut:
        """
        Retrieve a folder by its ID, or raise NoResultFound.
        """
        db_item: FolderDB = await self.repo.get_by_virtual_path(path)
        return FolderOut.model_validate(db_item.model_dump())

    async def create(self, data: FolderIn) -> FolderOut:
        """
        Create folder on disk and in DB, return FolderOut.
        """
        # virtual_path

        if data.parent_id:
            parent = await self.repo.get_by_id(data.parent_id)
            virt = parent.virtual_path.rstrip("/") + f"/{data.name}/"
        else:
            virt = self.base_virtual + f"{data.name}/"

        try:
            await self.repo.get_by_virtual_path(virt)
        except NoResultFound:
            pass
        else:
            raise FolderAlreadyExistsError(virt)

        # physical path
        phys_path = self.disk.compute_storage_path(virt)
        await self.disk.create_folder(phys_path)

        # persist
        db_item: FolderDB = await self.repo.create(
            data,
            storage_path=str(phys_path),
            virtual_path=virt
        )
        return FolderOut.model_validate(db_item.model_dump())

    async def update(self, folder_id: UUID, data: FolderUpdate) -> FolderOut:
        """
        Update folder metadata and disk, return FolderOut.
        """
        existing: FolderDB = await self.repo.get_by_id(folder_id)

        new_name = data.name or existing.name
        # determine new virtual path
        if data.parent_id is not None:
            if data.parent_id:
                new_parent = await self.repo.get_by_id(data.parent_id)
                base_virt = new_parent.virtual_path.rstrip("/")
            else:
                base_virt = self.base_virtual.rstrip("/")
            new_virt = f"{base_virt}/{new_name}/"
        else:
            virt_parent = existing.virtual_path.rstrip("/").rsplit("/", 1)[0]
            new_virt = f"{virt_parent}/{new_name}/"

        # rename on disk if changed
        old_path = Path(existing.storage_path)
        new_path = self.disk.compute_storage_path(new_virt)
        if str(old_path) != str(new_path):
            await self.disk.rename_folder(old_path, new_path)

        # update in DB
        updated_db: FolderDB = await self.repo.update(
            folder_id,
            data,
            storage_path=str(new_path),
            virtual_path=new_virt
        )
        return FolderOut.model_validate(updated_db.model_dump())

    async def delete(self, folder_id: UUID) -> None:
        """
        Remove folder both from disk and database.
        """
        existing: FolderDB = await self.repo.get_by_id(folder_id)
        await self.disk.delete_folder(Path(existing.storage_path))
        await self.repo.delete(folder_id)
