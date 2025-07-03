from loguru import logger
from contextlib import asynccontextmanager
import uvicorn
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from app.core.admin import init_admin

from app import api
from app.core.config import settings
from app.db.session import sessionmanager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await sessionmanager.test_connection()
        logger.info("DB connection created successfully")
    except Exception:
        logger.error(f"DB connection failed: {settings.POSTGRES_ASYNC_URL}")
    yield

app = FastAPI(
    lifespan=lifespan,
    docs_url="/api/docs",
)

init_admin(app)

add_pagination(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.healthcheck_router)
app.include_router(api.folder_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
