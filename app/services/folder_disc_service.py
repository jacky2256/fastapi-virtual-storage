import shutil
from pathlib import Path
import asyncio


class FolderDiskService:
    """
    Асинхронный сервис для работы с папками на файловой системе.
    Все методы не блокируют event loop, а выполняются в пуле потоков.
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def compute_storage_path(self, virtual_path: str) -> Path:
        """
        Правильно конструирует Path из base_path и виртуального пути.
        """
        # 1) Разбиваем виртуальный путь на сегменты
        parts = [segment for segment in virtual_path.strip("/").split("/") if segment]
        # 2) Склеиваем base_path и все сегменты
        return Path(self.base_path, *parts)

    async def exists(self, path: Path) -> bool:
        """
        Проверяет, существует ли папка. Выполняется в отдельном потоке.
        """
        return await asyncio.to_thread(path.is_dir)

    async def create_folder(self, path: Path) -> None:
        """
        Создаёт папку и все родительские директории. Если уже есть — FileExistsError.
        """
        def _mkdir():
            path.mkdir(parents=True, exist_ok=False)
        await asyncio.to_thread(_mkdir)

    async def delete_folder(self, path: Path) -> None:
        """
        Рекурсивно удаляет папку. Если нет — пропускает.
        """
        def _rmtree():
            if path.exists():
                shutil.rmtree(path)
        await asyncio.to_thread(_rmtree)

    async def rename_folder(self, old_path: Path, new_path: Path) -> None:
        """
        Переименовывает (перемещает) папку, создавая при необходимости родителя.
        """
        def _rename():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            old_path.rename(new_path)
        await asyncio.to_thread(_rename)
