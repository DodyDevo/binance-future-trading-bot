from math import floor
from typing import Any, Optional

from binance.error import ClientError
from service import setting as Setting
from service import api_client, get_logger

log = get_logger(__name__)


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


async def get_max_value(
    symbol: str,
    timout: Optional[int] = Setting.BINANCE_TIMEOUT,
    leverage: Optional[int] = Setting.LEVERAGE,
) -> float:
    try:
        response = api_client.change_leverage(
            symbol=symbol, leverage=leverage, recWindow=timout
        )
        return float(response["maxNotionalValue"])
    except ClientError as error:
        log.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        return -1


async def allowable(
    symbol: str,
    entry: float,
    leverage: int = Setting.LEVERAGE,
) -> tuple[Any, int | None]:
    try:
        while True:
            max_value = await get_max_value(symbol=symbol, leverage=leverage)
            price = float(api_client.mark_price(symbol=symbol)["markPrice"])
            quantity = (Setting.TRADE_AMOUNT * leverage) / entry
            total = quantity * price
            if total <= max_value:
                return (quantity, leverage)

            if leverage > 5:
                leverage = leverage - 5
            else:
                leverage = leverage - 1
    except ClientError as error:
        log.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        return (-1, -1)


async def set_margin_type(margin_type: str, symbol: str) -> None:
    try:
        api_client.change_margin_type(
            symbol=symbol, marginType=margin_type, recWindow=10000
        )
    except ClientError as error:
        log.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )


async def check_balance() -> float:
    try:
        assets = api_client.balance()
        for asset in assets:
            if asset["asset"] == "USDT":
                return float(asset["availableBalance"])
        return -1
    except ClientError as error:
        log.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        return -1


def create_order(param: list[dict]) -> dict:
    try:
        response = api_client.new_batch_order(param)
        return response
    except ClientError as error:
        log.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        return {}


def auto_cancel_order(symbol: str, milliseconds: int = 14400000) -> None:
    try:
        api_client.countdown_cancel_order(symbol=symbol, countdownTime=milliseconds)
    except ClientError as error:
        log.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
