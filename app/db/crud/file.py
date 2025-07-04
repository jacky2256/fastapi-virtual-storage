# app/db/crud/file.py

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound, IntegrityError

from app.db.models import File as FileORM
from app.schemas.file import FileIn, FileUpdate, FileDB


class FileRepository:
    """
    Repository for performing CRUD operations on File entities.

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
        data: FileIn,
        storage_path: str,
        virtual_path: str,
        size_bytes: int = 0,
        mime_type: str = "",
        file_id: Optional[UUID] = None,
    ) -> FileDB:
        """
        Create a new File record in the database.

        :param data: DTO containing input fields for the new file
        :param storage_path: the physical path on disk where the file is stored
        :returns: a FileDB schema with all fields populated (including id, timestamps)
        :raises: IntegrityError if constraints are violated
        """
        file = FileORM(
            id=file_id,
            name=data.name,
            virtual_path=virtual_path,
            uploader_user_id=data.uploader_user_id,
            folder_id=data.folder_id,
            storage_path=storage_path,
            size_bytes=size_bytes,
            mime_type=mime_type,
        )
        self.session.add(file)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(file)
        return FileDB.model_validate(file)

    async def get_by_id(self, file_id: UUID) -> FileDB:
        """
        Retrieve a single File by its ID.

        :param file_id: the UUID of the file to fetch
        :returns: FileDB if found
        :raises: NoResultFound if no matching record exists
        """
        q = await self.session.execute(
            select(FileORM).where(FileORM.id == file_id)
        )
        file = q.scalar_one_or_none()
        if file is None:
            raise NoResultFound(f"File with id {file_id} not found")
        return FileDB.model_validate(file)

    async def get_by_path(self, file_path: str) -> FileDB:
        """
        Retrieve a single File by its Path.

        :param file_path: the virtual path of the file to fetch
        :returns: FileDB if found
        :raises: NoResultFound if no matching record exists
        """
        q = await self.session.execute(
            select(FileORM).where(FileORM.virtual_path == file_path)
        )
        file = q.scalar_one_or_none()
        if file is None:
            raise NoResultFound(f"File with path {file_path} not found")
        return FileDB.model_validate(file)

    async def list_by_folder(self, folder_id: Optional[UUID]) -> List[FileDB]:
        """
        List all files under a given folder.

        :param folder_id: the UUID of the parent folder, or None for unassigned
        :returns: a list of FileDB objects ordered by name
        """
        q = await self.session.execute(
            select(FileORM)
            .where(FileORM.folder_id == folder_id)
            .order_by(FileORM.name)
        )
        return [FileDB.model_validate(f) for f in q.scalars().all()]

    async def update(
        self,
        file_id: UUID,
        data: FileUpdate,
        storage_path: Optional[str] = None,
        size_bytes: Optional[int] = None,
        mime_type: Optional[str] = None,
    ) -> FileDB:
        """
        Partially update fields of an existing File.

        Any fields not present in `data` will remain unchanged.
        Optionally override storage_path, size_bytes, or mime_type if provided.

        :param file_id: the UUID of the file to update
        :param data: DTO containing fields to update
        :param storage_path: new physical path on disk, if moved/renamed
        :param size_bytes: new size in bytes, if re-calculated
        :param mime_type: new MIME type, if re-detected
        :returns: updated FileDB
        :raises: NoResultFound if no such file existed
        """
        values = data.model_dump(exclude_unset=True)
        if storage_path is not None:
            values["storage_path"] = storage_path
        if size_bytes is not None:
            values["size_bytes"] = size_bytes
        if mime_type is not None:
            values["mime_type"] = mime_type

        result = await self.session.execute(
            update(FileORM)
            .where(FileORM.id == file_id)
            .values(**values)
        )
        if result.rowcount == 0:
            raise NoResultFound(f"File with id {file_id} not found")
        await self.session.commit()
        return await self.get_by_id(file_id)

    async def delete(self, file_id: UUID) -> None:
        """
        Delete a File record by its ID, then commit.

        :param file_id: the UUID of the file to delete
        :raises: NoResultFound if no row was deleted
        """
        result = await self.session.execute(
            delete(FileORM).where(FileORM.id == file_id)
        )
        if result.rowcount == 0:
            raise NoResultFound(f"File with id {file_id} not found")
        await self.session.commit()
