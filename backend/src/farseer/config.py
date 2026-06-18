import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    environment: str = "dev"  # dev or prod

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/farseer"
    database_url_sync: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/farseer"

    # API
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8173

    # Path prefix (for nginx reverse proxy)
    root_path: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Tushare
    tushare_token: str = ""
    tushare_api_url: str = ""  # Custom mirror URL (empty = official)

    # API Key
    api_key: str = ""

    # Scheduler
    enable_scheduler: bool = True  # Only production runs daily fetch

    model_config = {
        "env_file": os.environ.get("ENV_FILE", ".env.dev"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def is_dev(self) -> bool:
        return self.environment == "dev"

    @property
    def is_prod(self) -> bool:
        return self.environment == "prod"


settings = Settings()
