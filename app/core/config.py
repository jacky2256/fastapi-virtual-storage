from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    SERVICE_NAME: str = "fjc_rs_core_service"
    DEBUG: bool = True

    POSTGRES_SYNC_URL: str = 'postgresql://jacky:1234@localhost:5438/vs_db'
    POSTGRES_ASYNC_URL: str = 'postgresql+asyncpg://jacky:1234@localhost:5438/vs_db'

    STORAGE_BASE_PATH: str = '/home/jacky/Projects/learn_projects/fastapi_virtual_storage/tmp'
    VIRTUAL_BASE_PATH: str = '/'

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / '.env', BASE_DIR / '.env.prod'),
        env_file_encoding='utf-8',
        extra = 'ignore'
    )


settings = Settings()


