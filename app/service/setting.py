from pydantic import Field
from pydantic_settings import BaseSettings


class Setting(BaseSettings):
    TELEGRAM_TOKEN: str
    TELEGRAM_OWNER_ID: int

    BINANCE_BASE_URL: str
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    BINANCE_TIMEOUT: int = Field(10000, ge=5000)

    TARGET: int = Field(3, ge=1, le=6)
    TRADE_AMOUNT: float = Field(1, gt=0)
    LEVERAGE: int = Field(10, ge=1, le=125)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


setting = Setting()
