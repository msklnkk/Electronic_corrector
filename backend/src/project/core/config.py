from pydantic_settings import BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    ORIGINS: str = ''
    ROOT_PATH: str = ''
    ENV: str = ''
    LOG_LEVEL: str = ''

    POSTGRES_SCHEMA: str = 'my_app_schema'
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_DB: str = 'postgres'
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: SecretStr = 'postgres'
    POSTGRES_PASSWORD: SecretStr = 'postgres'
    POSTGRES_RECONNECT_INTERVAL_SEC: int = 1
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_AUTH_KEY: SecretStr = ''
    AUTH_ALGORITHM: str = ''

    @property
    def postgres_url(self) -> str:
        creds = f"{self.POSTGRES_USER.get_secret_value()}:{self.POSTGRES_PASSWORD.get_secret_value()}"
        return f"postgresql+asyncpg://{creds}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
