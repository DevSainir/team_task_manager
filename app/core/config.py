from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Team Task Manager"
    VERSION: str = "1.0.0"

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION_NAME: str
    AWS_S3_BUCKET_NAME: str
    AWS_S3_BASE_URL: str
    AWS_PRESIGN_EXPIRES_SECONDS: int = 3600
    S3_ENDPOINT_URL: str | None = None

    MINIO_ROOT_USER: str | None = None
    MINIO_ROOT_PASSWORD: str | None = None
    MINIO_BUCKET_NAME: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
