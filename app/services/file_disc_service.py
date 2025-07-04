import shutil
from pathlib import Path
import asyncio
import mimetypes
from typing import Optional, List, BinaryIO


class FileDiskService:
    """
    Async-capable service for saving, deleting and processing files on disk.
    """

    def __init__(
        self,
        base_path: Path,
        allowed_extensions: Optional[List[str]] = None
    ):
        """
        :param base_path: root of the storage area
        :param allowed_extensions: if given, only files with these extensions are permitted (e.g. ['.jpg','.png','.mp4'])
        """
        self.base_path = base_path
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions] if allowed_extensions else None

    def compute_file_path(self, virtual_path: str, filename: str) -> Path:
        """
        Build the physical path for a given virtual directory + filename.
        """
        parts = [seg for seg in virtual_path.strip("/").split("/") if seg]
        return Path(self.base_path, *parts, filename)

    async def save_file(self, stream: BinaryIO, virtual_path: str, filename: str) -> Path:
        """
        Save an uploaded file (binary stream) to disk, ensuring directories exist.
        Returns the Path to the saved file.
        :raises: ValueError if extension not allowed.
        """
        path = self.compute_file_path(virtual_path, filename)
        ext = path.suffix.lower()
        if self.allowed_extensions is not None and ext not in self.allowed_extensions:
            raise ValueError(f"Extension '{ext}' not allowed")

        # write in thread
        def _write():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as f:
                shutil.copyfileobj(stream, f)
        await asyncio.to_thread(_write)
        return path

    async def delete_file(self, path: Path) -> None:
        """
        Delete a file if it exists.
        """
        def _unlink():
            if path.exists():
                path.unlink()
        await asyncio.to_thread(_unlink)

    async def get_mime_type(self, path: Path) -> str:
        """
        Detect mime type by extension or content.
        """
        mime, _ = mimetypes.guess_type(str(path))
        return mime or "application/octet-stream"
