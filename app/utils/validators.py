from typing_extensions import Annotated

from pydantic import Field
from pydantic.functional_validators import AfterValidator


def validate_no_slash(name: str) -> str:
    """
    Ensure that the provided folder name does not contain '/'.
    """
    if "/" in name:
        raise ValueError("Folder name cannot contain '/'")
    return name

FolderName = Annotated[
    str,
    Field(
            min_length=1,
            max_length=100,
            description="Название папки (1–100 символов, без '/')"
        ),
    AfterValidator(validate_no_slash)
]

