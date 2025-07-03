from fastapi import APIRouter, HTTPException, status as http_status

router = APIRouter(tags=["Healthcheck"], prefix="/v1/healthcheck")


@router.get(
    "/",
    responses={
        200: {"description": "Test successful"},
        500:  {"description": "Test failed"},
    }
)
async def healthcheck():
    try:
        return {'healthy': True}
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )



