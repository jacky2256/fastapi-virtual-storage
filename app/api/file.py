# app/api/files.py

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.schemas.file import FileIn, FileOut, FileUpdate
from app.services import FileService
from app.dependencies import get_file_service

router = APIRouter(
    prefix="/files",
    tags=["Files"]
)

@router.get(
    "/download/by-path",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "File not found"},
        500: {"description": "Internal server error"},
    },
    summary="Download a file by its path",
)
async def download_file_by_path(
    file_path: str,
    service: FileService = Depends(get_file_service),
):
    """
    Download a file given its UUID.
    """
    try:
        file_out = await service.get_file_info_for_download(file_path)
        return FileResponse(
            path=file_out.storage_path,
            filename=file_out.name,
            media_type=file_out.mime_type or "application/octet-stream",
        )
    except NoResultFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/",
    response_model=List[FileOut],
    status_code=status.HTTP_200_OK,
    responses={500: {"description": "Internal server error"}},
    summary="List files in a folder",
)
async def list_files(
    folder_id: Optional[uuid.UUID] = None,
    service: FileService = Depends(get_file_service),
) -> List[FileOut]:
    """
    List all files under the specified folder.
    If `folder_id` is omitted, lists all unassigned files.
    """
    try:
        return await service.list(folder_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/upload",
    response_model=FileOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "File uploaded successfully"},
        400: {"description": "Bad request / extension not allowed"},
        409: {"description": "Database conflict"},
        500: {"description": "Internal server error"},
    },
    summary="Upload a new file",
)
async def upload_file(
    file: UploadFile,
    uploader_user_id: uuid.UUID = Form(..., description="Uploader's UUID"),
    folder_path: str = Form(..., description="Virtual path for the file"),
    service: FileService = Depends(get_file_service),
) -> FileOut:
    """
    Upload a file stream and save metadata.

    - **Form Data**:
      - `file` (UploadFile): The file to upload.
      - `uploader_user_id` (UUID): ID of uploading user.
      - `folder_path` str: Path of folder where the file will be stored.

    - **Response** (`FileOut`): Details of the stored file.
    """
    try:
        return await service.upload(
            file_name=file.filename,
            uploader_user_id=uploader_user_id,
            folder_path=folder_path,
            stream=file.file,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch(
    "/{file_id}",
    response_model=FileOut,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "File metadata updated"},
        404: {"description": "File not found"},
        409: {"description": "Conflict renaming or DB constraint"},
        500: {"description": "Internal server error"},
    },
    summary="Update file metadata",
)
async def update_file(
    file_id: uuid.UUID,
    file_update: FileUpdate,
    service: FileService = Depends(get_file_service),
) -> FileOut:
    """
    Update metadata of an existing file (name, folder).
    """
    try:
        return await service.update_metadata(file_id, file_update)
    except NoResultFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete(
    "/by-path",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "File deleted successfully"},
        404: {"description": "File not found"},
        500: {"description": "Internal server error"},
    },
    summary="Delete a file by its Path",
)
async def delete_file(
    file_path: str,
    service: FileService = Depends(get_file_service),
) -> None:
    """
    Delete a file given its Path.
    """
    try:
        await service.delete_file_by_path(file_path)
    except NoResultFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
