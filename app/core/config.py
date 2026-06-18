from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configured settings"""

    PROJECT_NAME: str = "Team Task Manager"
    VERSION: str = "1.0.0"

    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int = 5432
    DATABASE_URL: str | None = None

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION_NAME: str | None = None
    AWS_S3_BUCKET_NAME: str | None = None
    AWS_S3_BASE_URL: str | None = None
    AWS_PRESIGN_EXPIRES_SECONDS: int = 3600
    S3_ENDPOINT_URL: str | None = None

    MINIO_ROOT_USER: str | None = None
    MINIO_ROOT_PASSWORD: str | None = None
    MINIO_BUCKET_NAME: str | None = None
    MINIO_REGION_NAME: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def assemble_database_url(self) -> "Settings":
        """Prioritize given url and adapting for async"""
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgresql://"):
                self.DATABASE_URL = self.DATABASE_URL.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )
        else:
            self.DATABASE_URL = f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

        return self


settings = Settings()
