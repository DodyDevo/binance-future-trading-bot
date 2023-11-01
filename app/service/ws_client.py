import json
import asyncio
from time import sleep
from datetime import datetime

from telegram import Bot
from handler import create_order, auto_cancel_order
from binance.websocket.binance_socket_manager import BinanceSocketManager
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient

from .logger import get_logger
from .api_client import api_client
from .setting import setting as Setting

log = get_logger(__name__)

listen_key = ""
bot = Bot(token=Setting.TELEGRAM_TOKEN)


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

            if message_order["o"] == "TAKE_PROFIT_MARKET":
                auto_cancel_order(symbol=symbol, milliseconds=5000)
                asyncio.run(
                    bot.send_message(
                        chat_id=Setting.TELEGRAM_CHAT_ID,
                        text=f"Take profit order filled for #{symbol}",
                    )
                )
            elif message_order["o"] == "STOP_MARKET":
                auto_cancel_order(symbol=symbol, milliseconds=5000)
                asyncio.run(
                    bot.send_message(
                        chat_id=Setting.TELEGRAM_CHAT_ID,
                        text=f"Stop loss order filled for #{symbol}",
                    )
                )
            elif message_order["o"] == "MARKET":
                api_client.cancel_open_orders(symbol=symbol)
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
                        "recvWindow": str(Setting.BINANCE_TIMEOUT),
                    },
                ]

                orders = create_order(param)
                auto_cancel_order(symbol=symbol, milliseconds=432000000)

                is_take_profit_success = orders[0].get("code", None)
                is_stop_loss_success = orders[1].get("code", None)

                if is_take_profit_success is None and is_stop_loss_success is None:
                    asyncio.run(
                        bot.send_message(
                            chat_id=Setting.TELEGRAM_CHAT_ID,
                            text=f"TP/SP order created for #{symbol}",
                        )
                    )
                else:
                    asyncio.run(
                        bot.send_message(
                            chat_id=Setting.TELEGRAM_CHAT_ID,
                            text=f"TP/SP order fail for {symbol}"
                            f"\ndetails: {json.dumps(orders, indent=4)}",
                        )
                    )

            else:
                log.debug(f"Message received: {message}")

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
        sleep(3950)
