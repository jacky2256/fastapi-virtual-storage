# app/api/folders.py

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.schemas.folder import FolderIn, FolderOut, FolderUpdate
from app.services.folder_service import FolderService
from app.dependencies import get_folder_service

router = APIRouter(
    prefix="/folders",
    tags=["Folders"]
)


@router.get(
    "/{folder_id}",
    response_model=FolderOut,
    status_code=http_status.HTTP_200_OK,
    responses={
        404: {"description": "Folder not found"},
        500: {"description": "Internal server error"},
    }
)
async def get_folder_by_id(
    folder_id: uuid.UUID,
    service: FolderService = Depends(get_folder_service),
) -> FolderOut:
    """
    Retrieve a folder by its unique ID.

    - **Path Parameter**:
      - `folder_id` (UUID): The unique identifier of the folder to retrieve.

    - **Response Model** (`FolderOut`):
      | Field           | Type     | Description                                  |
      |-----------------|----------|----------------------------------------------|
      | `id`            | UUID     | Unique identifier of the folder              |
      | `name`          | string   | Name of the folder                           |
      | `parent_id`     | UUID     | ID of the parent folder, or `null` if root   |
      | `creator_user_id` | UUID   | ID of the user who created the folder        |
      | `is_published`  | bool     | Visibility flag for unauthenticated users    |
      | `virtual_path`  | string   | Virtual path of the folder on the website    |
      | `created_at`    | datetime | Timestamp when the folder was created        |
      | `updated_at`    | datetime | Timestamp when the folder was last updated   |

    - **Responses**:
      - **200 OK**: Folder was successfully retrieved.
      - **404 Not Found**: No folder found with the given ID.
      - **500 Internal Server Error**: Unexpected error occurred.
    """
    try:
        return await service.get_folder_by_id(folder_id)
    except NoResultFound as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/",
    response_model=List[FolderOut],
    status_code=http_status.HTTP_200_OK,
    responses={
        500: {"description": "Internal server error"},
    }
)
async def list_folders(
    parent_id: Optional[uuid.UUID] = None,
    service: FolderService = Depends(get_folder_service),
) -> List[FolderOut]:
    """
    List child folders under a given parent.

    - **Query Parameter**:
      - `parent_id` (UUID, optional): The ID of the parent folder.
        If omitted or null, returns root-level folders.

    - **Response Model** (`List[FolderOut]`):
      A JSON array of folder objects as described in **FolderOut** above.

    - **Responses**:
      - **200 OK**: List of folders returned successfully.
      - **500 Internal Server Error**: Unexpected error occurred.
    """
    try:
        return await service.list(parent_id)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/",
    response_model=FolderOut,
    status_code=http_status.HTTP_201_CREATED,
    responses={
        201: {"description": "Folder created successfully."},
        409: {"description": "Folder already exists or conflict."},
        500: {"description": "Internal server error."},
    }
)
async def create_folder(
    folder_in: FolderIn,
    service: FolderService = Depends(get_folder_service),
) -> FolderOut:
    """
    Create a new folder.

    - **Request Body** (`FolderIn`):
      | Field             | Type   | Required | Description                                  |
      |-------------------|--------|----------|----------------------------------------------|
      | `name`            | string | Yes      | Name of the new folder                       |
      | `parent_id`       | UUID   | No       | ID of the parent folder (null for root)      |
      | `creator_user_id` | UUID   | Yes      | ID of the user creating this folder          |
      | `is_published`    | bool   | No       | Visibility for unauthenticated users (default: true) |

    - **Response Model** (`FolderOut`): Returns the newly created folder.

    - **Responses**:
      - **201 Created**: Folder was created successfully.
      - **409 Conflict**: A folder with the same virtual path already exists.
      - **500 Internal Server Error**: Unexpected error during creation.
    """
    try:
        return await service.create(folder_in)
    except FileExistsError as e:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Folder already exists: {e}",
        )
    except IntegrityError as e:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Database constraint error: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch(
    "/{folder_id}",
    response_model=FolderOut,
    status_code=http_status.HTTP_200_OK,
    responses={
        200: {"description": "Folder updated successfully."},
        404: {"description": "Folder not found."},
        409: {"description": "Filesystem or database conflict."},
        500: {"description": "Internal server error."},
    }
)
async def update_folder(
    folder_id: uuid.UUID,
    folder_update: FolderUpdate,
    service: FolderService = Depends(get_folder_service),
) -> FolderOut:
    """
    Update an existing folder by its ID.

    - **Path Parameter**:
      - `folder_id` (UUID): ID of the folder to update.

    - **Request Body** (`FolderUpdate`):
      | Field          | Type   | Required | Description                                     |
      |----------------|--------|----------|-------------------------------------------------|
      | `name`         | string | No       | New name of the folder (optional)               |
      | `parent_id`    | UUID   | No       | New parent folder ID (optional)                 |
      | `creator_user_id` | UUID| No       | (Usually unchanged)                             |
      | `is_published` | bool   | No       | Visibility flag (optional)                      |

    - **Response Model** (`FolderOut`): Returns the updated folder.

    - **Responses**:
      - **200 OK**: Folder updated successfully.
      - **404 Not Found**: No folder with the given ID.
      - **409 Conflict**: Error renaming/moving folder on disk or DB constraint.
      - **500 Internal Server Error**: Unexpected error during update.
    """
    try:
        return await service.update(folder_id, folder_update)
    except NoResultFound as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except FileExistsError as e:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Filesystem operation failed: {e}",
        )
    except IntegrityError as e:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Database constraint error: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{folder_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Folder deleted successfully."},
        404: {"description": "Folder not found."},
        500: {"description": "Internal server error."},
    }
)
async def delete_folder(
    folder_id: uuid.UUID,
    service: FolderService = Depends(get_folder_service),
) -> None:
    """
    Delete a folder by its ID.

    - **Path Parameter**:
      - `folder_id` (UUID): The unique identifier of the folder to delete.

    - **Responses**:
      - **204 No Content**: Folder deleted successfully.
      - **404 Not Found**: No folder found with the given ID.
      - **500 Internal Server Error**: Unexpected error during deletion.
    """
    try:
        await service.delete(folder_id)
    except NoResultFound as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
