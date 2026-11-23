from functools import lru_cache

from pydantic import FilePath, SecretStr
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

    constellation_filepath: FilePath

    simulation_tick_seconds: float = 0.01

    rabbitmq_host: str
    rabbitmq_port: int = 5672
    rabbitmq_user: str
    rabbitmq_password: SecretStr
    rabbitmq_vhost: str = "/"
    rabbitmq_exchange: str = "orbit.events"
    rabbitmq_publish_timeout_seconds: float = 5.0

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
