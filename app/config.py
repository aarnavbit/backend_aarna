from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union, Optional
import os

class Settings(BaseSettings):
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DB_PATH: str = "data.db"
    DATABASE_URL: Optional[str] = None
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    ADMIN_PASSWORD: str = "admin123"
    SECRET_KEY: str = "aarna_recruitment_jwt_secret_key_2026"
    DEFAULT_SUPERADMIN_ROLL: str = "ADMIN001"
    DEFAULT_SUPERADMIN_PASS: str = "adminpassword123"
    WHATSAPP_GROUP_LINK: str = "https://chat.whatsapp.com/"
    CORS_ORIGINS: Union[str, List[str]] = ["*"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

    @property
    def resolved_database_url(self) -> str:
        raw_url = self.DATABASE_URL or self.SQLALCHEMY_DATABASE_URI or os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
        if raw_url:
            if raw_url.startswith("postgres://"):
                return raw_url.replace("postgres://", "postgresql://", 1)
            return raw_url
        return f"sqlite:///{self.DB_PATH}"

settings = Settings()
