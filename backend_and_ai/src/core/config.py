from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/remitout_crm"
    # Comma-separated Fernet keys. First encrypts; all can decrypt (enables key rotation).
    encryption_keys: str = ""
    # Shared secret for the X-Admin-Key header. Empty = all protected routes refuse requests.
    admin_api_key: str = ""
    # Upstash (or any Redis): rediss://default:<password>@<host>:6379. Empty = caching disabled.
    redis_url: str = ""
    cache_prefix: str = "remitout"
    cache_ttl_seconds: int = 300  # safety net; normal freshness comes from delete-on-write
    cache_reference_ttl_seconds: int = 3600
    max_upload_bytes: int = 2 * 1024 * 1024
    edubao_staging_url: str = "https://api.edubao.lifeinurl.com"
    edubao_production_url: str = "https://crmapi.edubao.org"


settings = Settings()
