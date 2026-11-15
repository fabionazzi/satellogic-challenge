from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    """Application settings loaded from environment variables / env/.env."""

    model_config = SettingsConfigDict(
        env_file="env/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_host: str = "0.0.0.0"
    app_port: int = 8080

    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: SecretStr
    mysql_database: str

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="mysql+aiomysql",
            username=self.mysql_user,
            password=self.mysql_password.get_secret_value(),
            host=self.mysql_host,
            port=self.mysql_port,
            database=self.mysql_database,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
