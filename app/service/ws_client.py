from time import sleep
from datetime import datetime

from binance.websocket.binance_socket_manager import BinanceSocketManager
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient

from .logger import get_logger
from .api_client import api_client
from .setting import setting as Setting

log = get_logger(__name__)

listen_key = ""


def message_handler(_: BinanceSocketManager, message: dict) -> None:
    print(message)


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
