# app/db/crud/folder.py

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi_pagination.ext.sqlalchemy import apaginate
from fastapi_pagination import Page

from app.db.models import Folder as FolderORM
from app.schemas import FolderIn, FolderUpdate, FolderDB, PaginationParamsSchema, FolderOut


class FolderRepository:
    """
    Repository for performing CRUD operations on Folder entities.

    All methods assume an AsyncSession is provided and manage only
    database interactions (no file‐system operations).

    :param session: an instance of AsyncSession bound to the engine
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with an AsyncSession.
        """
        self.session = session

    async def create(
        self,
        data: FolderIn,
        storage_path: str,
        virtual_path: str
    ) -> FolderDB:
        """
        Create a new Folder record in the database.

        :param data: DTO containing input fields for the new folder
        :param storage_path: the physical path on disk where the folder will live
        :param virtual_path: the virtual URL/path under which the folder is exposed
        :returns: a FolderDB schema with all fields populated (including id, timestamps)
        :raises: IntegrityError if constraints are violated
        """
        folder = FolderORM(
            name=data.name,
            parent_id=data.parent_id,
            creator_user_id=data.creator_user_id,
            is_published=data.is_published,
            storage_path=storage_path,
            virtual_path=virtual_path
        )
        self.session.add(folder)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(folder)
        return FolderDB.model_validate(folder)

    async def get_by_id(self, folder_id: UUID) -> FolderDB:
        """
        Retrieve a single Folder by its ID.

        :param folder_id: the UUID of the folder to fetch
        :returns: FolderDB if found, or None if no matching record exists
        """
        q = await self.session.execute(
            select(FolderORM).where(FolderORM.id == folder_id)
        )
        folder = q.scalar_one_or_none()
        if folder is None:
            raise NoResultFound(f"Folder with id {folder_id} not found")
        return FolderDB.model_validate(folder)

    async def get_by_virtual_path(self, virtual_path: str) -> FolderDB:
        """
        Retrieve a single Folder by its ID.

        :param folder_id: the UUID of the folder to fetch
        :returns: FolderDB if found, or None if no matching record exists
        """
        q = await self.session.execute(
            select(FolderORM).where(FolderORM.virtual_path == virtual_path)
        )
        folder = q.scalar_one_or_none()
        if folder is None:
            raise NoResultFound(f"Folder with path {virtual_path} not found")
        return FolderDB.model_validate(folder)

    async def list_by_parent_paginated(
            self,
            parent_id: Optional[UUID],
            params: PaginationParamsSchema
    ) -> Page[FolderOut]:
        """
        Return a paginated list of child folders under a given parent.

        :param parent_id: parent folder UUID, or None for root
        :param params: PaginationParamsSchema (page, size, etc.)
        :returns: Page[FolderOut]
        """
        query = (
            select(FolderORM)
            .where(FolderORM.parent_id == parent_id)
            .order_by(FolderORM.name)
        )
        # use the async SQLAlchemy paginator
        page: Page[FolderOut] = await apaginate(self.session, query, params)
        return page

    async def update(
        self,
        folder_id: UUID,
        data: FolderUpdate,
        storage_path: Optional[str] = None,
        virtual_path: Optional[str] = None
    ) -> FolderDB:
        """
        Partially update fields of an existing Folder.

        Any fields not present in `data` will remain unchanged.
        Optionally override storage_path and virtual_path if provided.

        :param folder_id: the UUID of the folder to update
        :param data: DTO containing fields to update
        :param storage_path: new physical path on disk, if renamed/moved
        :param virtual_path: new virtual path, if renamed/moved
        :returns: updated FolderDB, or None if no such folder existed
        """
        values = data.model_dump(exclude_unset=True)
        if storage_path is not None:
            values["storage_path"] = storage_path
        if virtual_path is not None:
            values["virtual_path"] = virtual_path

        await self.session.execute(
            update(FolderORM)
            .where(FolderORM.id == folder_id)
            .values(**values)
        )
        await self.session.commit()
        return await self.get_by_id(folder_id)

    async def delete(self, folder_id: UUID) -> None:
        """
        Delete a Folder record by its ID, then commit.

        :param folder_id: the UUID of the folder to delete
        :raises NoResultFound: if no row was deleted
        """
        result = await self.session.execute(
            delete(FolderORM).where(FolderORM.id == folder_id)
        )
        # Check how many rows were affected
        if result.rowcount == 0:
            raise NoResultFound(f"Folder with id {folder_id} not found")
        # persist the deletion
        await self.session.commit()
