from pydantic import Field
from pydantic_settings import BaseSettings


class Setting(BaseSettings):
    TELEGRAM_TOKEN: str
    TELEGRAM_OWNER_ID: int

    TARGET: int = Field(3, ge=1, le=6)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


setting = Setting()
