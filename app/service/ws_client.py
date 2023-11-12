import json
import asyncio
from time import sleep
from datetime import datetime

from telegram import Bot
from handler import create_order
from binance.error import ClientError
from telegram.request import HTTPXRequest
from binance.websocket.binance_socket_manager import BinanceSocketManager
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient

from .logger import get_logger
from .api_client import api_client
from .setting import setting as Setting

log = get_logger(__name__)

ws_client: UMFuturesWebsocketClient = None
listen_key = ""


def message_handler(_: BinanceSocketManager, message: dict) -> None:
    try:
        if isinstance(message, str):  # type: ignore
            message = json.loads(message)  # type: ignore

        event = message.get("e", None)

        if event == "ORDER_TRADE_UPDATE":
            message_order = message["o"]
            if message_order["X"] == "FILLED":
                with open("database.json", "r") as file:
                    database = json.load(file)

                bot = Bot(
                    token=Setting.TELEGRAM_TOKEN,
                    request=HTTPXRequest(connection_pool_size=8),
                )

                symbol = message_order["s"]
                order_id = message_order["c"]
                order_type = message_order["ot"]

                if order_id == database[symbol]["order_id"]:
                    side = "SELL" if database[symbol]["side"] == "BUY" else "BUY"

                    param = [
                        {
                            "symbol": symbol,
                            "side": side,
                            "type": "TRAILING_STOP_MARKET",
                            "activationPrice": str(database[symbol]["target"]),
                            "quantity": str(database[symbol]["quantity"]),
                            "callbackRate": "0.5",
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
                            "recvWindow": str(Setting.BINANCE_TIMEOUT),
                        },
                    ]
                    orders = create_order(param)

                    is_take_profit_success = orders[0].get("code", None)
                    is_stop_loss_success = orders[1].get("code", None)

                    if is_take_profit_success is None and is_stop_loss_success is None:
                        asyncio.run(
                            bot.send_message(
                                chat_id=Setting.TELEGRAM_CHAT_ID,
                                text=f"TP/SL order created for #{symbol}",
                            )
                        )
                    else:
                        asyncio.run(
                            bot.send_message(
                                chat_id=Setting.TELEGRAM_CHAT_ID,
                                text=f"TP/SL order fail for #{symbol}"
                                f"\ndetails: {json.dumps(orders, indent=4)}",
                            )
                        )
                elif order_type == "TRAILING_STOP_MARKET":
                    asyncio.run(
                        bot.send_message(
                            chat_id=Setting.TELEGRAM_CHAT_ID,
                            text=f"Trailing stop order filled for #{symbol}",
                        )
                    )
                elif order_type == "STOP_MARKET":
                    asyncio.run(
                        bot.send_message(
                            chat_id=Setting.TELEGRAM_CHAT_ID,
                            text=f"Stop loss order filled for #{symbol}",
                        )
                    )
                else:
                    log.debug(f"Unrecognize order message: {message_order}")
            else:
                log.debug(f"Not filled order message: {message_order}")
        else:
            log.debug(f"Message received: {message}")
    except Exception as error:
        log.error(f"Found error: {error}")


def renew_session() -> None:
    global ws_client
    global listen_key
    while True:
        try:
            if ws_client:
                ws_client.stop()
            ws_client = UMFuturesWebsocketClient(
                stream_url=Setting.BINANCE_WS_BASE_URL, on_message=message_handler
            )
            listen_key = api_client.new_listen_key()["listenKey"]
            ws_client.user_data(
                listen_key=listen_key,
                id=int(datetime.now().timestamp()),
            )
            log.debug(f"Session renewed for {listen_key}")
            sleep(82800)
        except Exception as error:
            log.error(f"Found error: {error}")


def renew_key() -> None:
    global listen_key
    while True:
        try:
            api_client.renew_listen_key(listen_key)
            log.debug(f"Listen key renewed for {listen_key}")
            sleep(3300)
        except ClientError as error:
            log.error(
                f"Found error. status: {error.status_code}"
                f"\nError code: {error.error_code}"
                f"\nError message: {error.error_message}"
            )
        except Exception as error:
            log.error(f"Found error: {error}")
