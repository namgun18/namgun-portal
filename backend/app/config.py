from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "namgun.or.kr Portal"
    app_url: str = "https://namgun.or.kr"
    debug: bool = False
    secret_key: str = "CHANGE_ME"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://portal:portal@portal-db:5432/portal"

    # Domain
    domain: str = "namgun.or.kr"

    # File storage
    storage_root: str = "/storage"
    upload_max_size_mb: int = 5120

    # Stalwart Mail (JMAP)
    stalwart_url: str = "http://192.168.0.250:8080"
    stalwart_admin_user: str = "admin"
    stalwart_admin_password: str = ""

    # SMTP (noreply sender)
    smtp_host: str = "mail.namgun.or.kr"
    smtp_port: int = 587
    smtp_user: str = "noreply@namgun.or.kr"
    smtp_password: str = ""
    smtp_from: str = "noreply@namgun.or.kr"

    # Admin notification
    admin_emails: str = "namgun18@namgun.or.kr"  # comma-separated

    # Gitea
    gitea_url: str = "http://192.168.0.50:3000"
    gitea_token: str = ""

    # GeoIP
    geoip_db_path: str = "/app/data/GeoLite2-Country.mmdb"

    # Portal OAuth Provider (for Gitea etc.)
    oauth_clients_json: str = "{}"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
