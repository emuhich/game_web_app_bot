from datetime import datetime
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    BOT_TOKEN: str = "your_bot_token"
    BASE_SITE: str = "https://yourdomain.com"
    ADMIN_ID: int = 123456789

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "postgres"

    ALGORITHM: str = "HS256"
    SECRET_KEY: str = "secret"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    CACHE_TIMEOUT: int = 30
    # Добавлены недостающие ключи для админ-панели/auth
    ADMIN_SECRET: str = "supersecretkey_change_me"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    ENVIRONMENT: str = "production"
    DISABLE_CACHE_IN_DEV: bool = True

    # YooKassa config
    YOOKASSA_SHOP_ID: str = ""
    YOOKASSA_SECRET_KEY: str = ""
    YOOKASSA_TEST_MODE: bool = True

    PREMIUM_PRICE_RUB: float = 229.0
    BUILD_HASH: str = Field(default_factory=lambda: datetime.utcnow().strftime('%Y%m%d%H%M%S'))

    # Логирование
    LOG_LEVEL: str = "INFO"          # Базовый уровень логирования
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    LOG_DIR: Path = Path("logs")     # Каталог для логов внутри проекта/контейнера
    LOG_TO_CONSOLE: bool = True       # Логировать ли в stdout
    LOG_TO_FILE: bool = True          # Логировать ли в файлы

    # Path constants
    APP_DIR: Path = Path(__file__).resolve().parent  # /app
    PROJECT_ROOT: Path = APP_DIR.parent              # project root
    FRONTEND_DIR: Path = APP_DIR / 'frontend'
    STATIC_DIR: Path = FRONTEND_DIR / 'static'
    MEDIA_DIR: Path = PROJECT_ROOT / 'app/media'

    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
    )

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    def get_webhook_url(self) -> str:
        """Возвращает URL вебхука с кодированием специальных символов."""
        return f"{self.BASE_SITE}/webhook"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() in {"development", "dev"}


settings = Settings()
