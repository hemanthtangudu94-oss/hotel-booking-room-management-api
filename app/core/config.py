from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = Field(default="HS256", pattern="^HS256$")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0, le=1440)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


    
settings = Settings()