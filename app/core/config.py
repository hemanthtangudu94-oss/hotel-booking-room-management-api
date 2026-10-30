from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = Field(default="HS256", pattern="^HS256$")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0, le=1440)
    DATABASE_URL: str = "sqlite:///./hotel_booking.db"
    MAIN_ADMIN_USERNAME: str = Field(default="admin", min_length=3, max_length=50)
    MAIN_ADMIN_PASSWORD: SecretStr | None = Field(default=None, min_length=12)
    MAIN_ADMIN_EMAIL: str = "admin@example.com"
    MAIN_ADMIN_FULL_NAME: str = "Hotel Administrator"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


    
settings = Settings()