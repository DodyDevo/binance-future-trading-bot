from pydantic import Field
from pydantic_settings import BaseSettings


class Setting(BaseSettings):
    TELEGRAM_TOKEN: str
    TELEGRAM_OWNER_ID: int

    BINANCE_BASE_URL: str
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str

    TARGET: int = Field(3, ge=1, le=6)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


setting = Setting()
