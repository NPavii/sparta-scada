"""Application configuration for Sparta AI service."""
import os
import socket
from functools import lru_cache
from urllib.parse import urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ai_database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "scada"
    postgres_user: str = "scada"
    postgres_password: str = "scada"

    # Optional path to Rapid SCADA Cnl.xml for channel metadata enrichment.
    cnl_xml_path: str | None = None

    service_port: int = 8000

    @property
    def database_url(self) -> str:
        if self.ai_database_url:
            url = self.ai_database_url
        else:
            url = (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return _resolve_localhost(url)

    @property
    def channel_map_path(self) -> str | None:
        if self.cnl_xml_path:
            return self.cnl_xml_path
        default_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "scada-config", "SpartaDemo", "BaseXML", "Cnl.xml"
        )
        default_path = os.path.normpath(default_path)
        return default_path if os.path.exists(default_path) else None


def _resolve_localhost(url: str) -> str:
    """Replace Docker-internal hostnames with localhost when they do not resolve."""
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        return url
    try:
        socket.gethostbyname(host)
        return url
    except socket.gaierror:
        localhost_netloc = parsed.netloc.replace(host, "localhost")
        return urlunparse(parsed._replace(netloc=localhost_netloc))


@lru_cache
def get_settings() -> Settings:
    return Settings()
