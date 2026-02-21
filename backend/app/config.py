from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "namgun.or.kr Portal"
    app_url: str = "https://namgun.or.kr"
    debug: bool = False
    secret_key: str = "CHANGE_ME"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://portal:portal@portal-db:5432/portal"

    # Authentik OIDC
    oidc_issuer: str = "https://auth.namgun.or.kr/application/o/portal/"
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = "https://namgun.or.kr/api/auth/callback"
    oidc_admin_group: str = "authentik Admins"

    # File storage
    storage_root: str = "/storage"
    upload_max_size_mb: int = 1024

    # Stalwart Mail (JMAP)
    stalwart_url: str = "http://192.168.0.250:8080"
    stalwart_admin_user: str = "admin"
    stalwart_admin_password: str = ""

    # BigBlueButton
    bbb_url: str = "https://meet.namgun.or.kr/bigbluebutton/api"
    bbb_secret: str = ""

    # Authentik Server-Side Auth
    authentik_base_url: str = "https://auth.namgun.or.kr"
    authentik_flow_slug: str = "default-authentication-flow"

    # Authentik Admin API
    authentik_api_token: str = ""
    authentik_users_group_pk: str = ""
    authentik_admins_group_pk: str = ""

    # Gitea
    gitea_url: str = "http://192.168.0.50:3000"
    gitea_token: str = ""

    # Portal OAuth Provider (for Gitea etc.)
    oauth_clients_json: str = "{}"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
