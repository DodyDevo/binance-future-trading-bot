import json
from time import sleep
from datetime import datetime

from handler import create_order, auto_cancel_order
from binance.websocket.binance_socket_manager import BinanceSocketManager
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient

from .logger import get_logger
from .api_client import api_client
from .setting import setting as Setting

log = get_logger(__name__)

listen_key = ""


def message_handler(_: BinanceSocketManager, message: dict) -> None:
    if isinstance(message, str):  # type: ignore
        message = json.loads(message)  # type: ignore
    event: str = message.get("e", None)
    if event == "ORDER_TRADE_UPDATE":
        log.info("Event received: ORDER_TRADE_UPDATE")
        message_order = message["o"]
        if message_order["X"] == "FILLED":
            with open("database.json", "r") as file:
                database = json.load(file)

            symbol = message_order["s"]

            if (
                database[symbol]["target"] == message_order["sp"]
                or database[symbol]["stop"] == message_order["sp"]
            ):
                auto_cancel_order(symbol=symbol, milliseconds=2000)
                log.info("TP/SP cancel")
                return None

            side = "SELL" if database[symbol]["side"] == "BUY" else "BUY"
            param = [
                {
                    "symbol": symbol,
                    "side": side,
                    "type": "TAKE_PROFIT_MARKET",
                    "stopPrice": str(database[symbol]["target"]),
                    "closePosition": "true",
                    "workingType": "MARK_PRICE",
                    "recvWindow": str(Setting.BINANCE_TIMEOUT),
                },
                {
                    "symbol": symbol,
                    "side": side,
                    "type": "STOP_MARKET",
                    "stopPrice": str(database[symbol]["stop"]),
                    "closePosition": "true",
                    "workingType": "MARK_PRICE",
                    "recvWindow": "10000",
                },
            ]

            log.info(f"TP/SP order to be send: {param}")
            create_order(param)
            auto_cancel_order(symbol=symbol, milliseconds=432000000)
            log.info("TP/SP hit")
    else:
        log.debug(f"Message received: {message}")


ws_client = UMFuturesWebsocketClient(
    stream_url=Setting.BINANCE_WS_BASE_URL, on_message=message_handler
)

listen_key = api_client.new_listen_key()["listenKey"]
ws_client.user_data(
    listen_key=listen_key,
    id=int(datetime.now().timestamp()),
)


def renew_session() -> None:
    while True:
        listen_key = api_client.new_listen_key()["listenKey"]
        ws_client.user_data(
            listen_key=listen_key,
            id=int(datetime.now().timestamp()),
        )
        log.debug(f"New Listen key {listen_key}")
        log.info("Session created.")
        sleep(82800)


def renew_key() -> None:
    while True:
        api_client.renew_listen_key(listen_key)
        log.debug(f"Listen key renewed for {listen_key}")
        sleep(55)
