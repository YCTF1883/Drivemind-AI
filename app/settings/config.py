import os
import typing

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    VERSION: str = "0.1.0"
    APP_TITLE: str = "DriveMind AI"
    PROJECT_NAME: str = "DriveMind AI"
    APP_DESCRIPTION: str = "Enterprise AI R&D Operations Platform"

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    DEBUG: bool = True

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf"  # openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 day

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_MAX_TOKENS: int = 2048
    DEEPSEEK_TIMEOUT: float = 30.0

    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "drivemind"

    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    AUDIT_LOG_RETENTION_DAYS: int = 30
    AI_CONTEXT_RETENTION_DAYS: int = 30
    AI_CONTEXT_MAX_MESSAGES_PER_SESSION: int = 20
    AI_CONTEXT_RECENT_MESSAGES: int = 6

    @property
    def TORTOISE_ORM(self) -> dict:
        return build_tortoise_orm(self)


settings = Settings()


def build_tortoise_orm(settings_obj: Settings) -> dict:
    return {
        "connections": {
            "mysql": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "host": settings_obj.DB_HOST,
                    "port": settings_obj.DB_PORT,
                    "user": settings_obj.DB_USER,
                    "password": settings_obj.DB_PASSWORD,
                    "database": settings_obj.DB_NAME,
                    "charset": "utf8mb4",
                },
            },
        },
        "apps": {
            "models": {
                "models": ["app.models", "aerich.models"],
                "default_connection": "mysql",
            },
        },
        "use_tz": False,  # Whether to use timezone-aware datetimes
        "timezone": "Asia/Shanghai",  # Timezone setting
    }


TORTOISE_ORM = settings.TORTOISE_ORM
