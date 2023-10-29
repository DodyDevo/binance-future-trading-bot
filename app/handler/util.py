from math import floor

from binance.error import ClientError
from service import setting as Setting
from service import api_client, get_logger

log = get_logger(__name__)


async def is_user_not_authorized(user_id: int) -> bool:
    if user_id == Setting.TELEGRAM_OWNER_ID:
        return False
    log.warning(f"Unauthorized user {user_id} tried to access the bot")
    return True


async def truncate(float: float, precision: int) -> float:
    return floor(float * 10**precision) / 10**precision


async def get_symbol_info(requested_symbol: str) -> dict:
    try:
        symbols = api_client.exchange_info()["symbols"]
        for symbol in symbols:
            if requested_symbol == symbol["symbol"]:
                return symbol
        return {}
    except ClientError as error:
        log.error(
            f"Found error. status: {error.status_code}"
            f"\nError code: {error.error_code}"
            f"\nError message: {error.error_message}"
        )
        return {}
