class AppError(Exception):
    """Base class for all application‐level errors."""
    pass


class FolderAlreadyExistsError(AppError):
    """Raised when attempting to create a folder whose virtual_path already exists."""
    def __init__(self, virtual_path: str):
        super().__init__(f"Folder at '{virtual_path}' already exists")
