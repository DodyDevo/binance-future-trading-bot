import json
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timedelta

from telegram import Update
from service import get_logger
from telegram.ext import ContextTypes
from service import setting as Setting
from model import MessageType, MessageParser

from .util import (
    truncate,
    allowable,
    create_order,
    cancel_orders,
    check_balance,
    get_symbol_info,
    set_margin_type,
    auto_cancel_order,
)

log = get_logger(__name__)


async def process_get_ready(parser: MessageParser) -> dict:
    symbol_info = await get_symbol_info(parser.symbol)

    price_precision = symbol_info.get("pricePrecision", None)

    tick_size = 0.0
    for symbol_filter in symbol_info["filters"]:
        if symbol_filter["filterType"] == "PRICE_FILTER":
            tick_size = float(symbol_filter["tickSize"])

    if not price_precision:
        log.error(f"Price precision not found for symbol: {parser.symbol}")
        return {}

    parser.entry = await truncate(parser.entry, price_precision)
    temp = Decimal(str(parser.entry))
    parser.entry = float(temp - temp % Decimal(str(tick_size)))

    parser.target = await truncate(parser.target, price_precision)

    parser.second_target = await truncate(parser.second_target, price_precision)
    temp = Decimal(str(parser.second_target))
    parser.second_target = float(temp - temp % Decimal(str(tick_size)))

    parser.stop = await truncate(parser.stop, price_precision)

    quantity, leverage = await allowable(parser.symbol, parser.entry)
    quantity = await truncate(quantity, symbol_info.get("quantityPrecision", None))

    balance = await check_balance()

    if balance < Setting.TRADE_AMOUNT:
        log.error(
            f"Stop trading balance is less than {Setting.TRADE_AMOUNT}, "
            "current balance {balance}"
        )
        return {}

    await cancel_orders(parser.symbol)

    await set_margin_type(margin_type="CROSSED", symbol=parser.symbol)

    client_order_id = str(uuid4())

    order_data = {
        "order_id": client_order_id,
        "entry": parser.entry,
        "target": parser.target,
        "second_target": parser.second_target,
        "stop": parser.stop,
        "side": parser.side,
        "quantity": quantity,
        "leverage": leverage,
        "timestamp": int(datetime.now().timestamp()),
    }

    with open("database.json", "r") as file:
        data = json.load(file)

    with open("database.json", "w") as file:
        data[parser.symbol] = order_data
        json.dump(data, file, indent=4)

    param = [
        {
            "symbol": parser.symbol,
            "side": parser.side.value,
            "type": "STOP",
            "stopPrice": str(parser.entry),
            "quantity": str(quantity),
            "price": str(parser.entry),
            "workingType": "MARK_PRICE",
            "recvWindow": str(Setting.BINANCE_TIMEOUT),
            "newClientOrderId": client_order_id,
        },
    ]

    orders = create_order(param)

    if orders[0].get("code", None) is not None:
        return orders

    log.debug(f"Orders created: {orders}")

    auto_cancel_order(parser.symbol)

    return orders


async def process_opened(parser: MessageParser) -> dict:
    if Setting.IGNORE_OPEN_ORDER:
        return {}

    with open("database.json", "r") as file:
        data = json.load(file)

    data_symbol = data.get(parser.symbol, None)

    if data_symbol is not None:
        diffrence_time = datetime.now() - datetime.fromtimestamp(
            data_symbol["timestamp"]
        )

        if diffrence_time < timedelta(hours=5):
            return {}

    balance = await check_balance()

    if balance < Setting.TRADE_AMOUNT:
        log.error(
            f"Stop trading balance is less than {Setting.TRADE_AMOUNT}, "
            f"current balance {balance}"
        )
        return {}

    symbol_info = await get_symbol_info(parser.symbol)

    tick_size = 0.0
    for symbol_filter in symbol_info["filters"]:
        if symbol_filter["filterType"] == "PRICE_FILTER":
            tick_size = float(symbol_filter["tickSize"])

    price_precision = symbol_info.get("pricePrecision", None)

    if not price_precision:
        log.error(f"Price precision not found for symbol: {parser.symbol}")
        return {}

    parser.entry = await truncate(parser.entry, price_precision)
    temp = Decimal(str(parser.entry))
    parser.entry = float(temp - temp % Decimal(str(tick_size)))

    parser.target = await truncate(parser.target, price_precision)

    parser.second_target = await truncate(parser.second_target, price_precision)
    temp = Decimal(str(parser.second_target))
    parser.second_target = float(temp - temp % Decimal(str(tick_size)))

    parser.stop = await truncate(parser.stop, price_precision)

    quantity, leverage = await allowable(parser.symbol, parser.entry)
    quantity = await truncate(quantity, symbol_info.get("quantityPrecision", None))

    await set_margin_type(margin_type="CROSSED", symbol=parser.symbol)

    client_order_id = str(uuid4())

    order_data = {
        "order_id": client_order_id,
        "entry": parser.entry,
        "side": parser.side,
        "target": parser.target,
        "second_target": parser.second_target,
        "stop": parser.stop,
        "quantity": quantity,
        "leverage": leverage,
        "timestamp": int(datetime.now().timestamp()),
    }

    with open("database.json", "w") as file:
        data[parser.symbol] = order_data
        json.dump(data, file, indent=4)

    # param = [
    #     {
    #         "symbol": parser.symbol,
    #         "side": parser.side.value,
    #         "type": "MARKET",
    #         "quantity": str(quantity),
    #         "workingType": "MARK_PRICE",
    #         "recvWindow": str(Setting.BINANCE_TIMEOUT),
    #         "newClientOrderId": client_order_id,
    #     },
    # ]

    param = [
        {
            "symbol": parser.symbol,
            "side": parser.side.value,
            "type": "STOP",
            "stopPrice": str(parser.entry),
            "quantity": str(quantity),
            "price": str(parser.entry),
            "workingType": "MARK_PRICE",
            "recvWindow": str(Setting.BINANCE_TIMEOUT),
            "newClientOrderId": client_order_id,
        },
    ]

    orders = create_order(param)

    auto_cancel_order(parser.symbol, 120000)

    if orders[0].get("code", None) is not None:
        if orders[0]["code"] == -2021:
            auto_cancel_order(parser.symbol, 0)
            param = [
                {
                    "symbol": parser.symbol,
                    "side": parser.side.value,
                    "type": "MARKET",
                    "quantity": str(quantity),
                    "workingType": "MARK_PRICE",
                    "recvWindow": str(Setting.BINANCE_TIMEOUT),
                    "newClientOrderId": client_order_id,
                },
            ]
            orders = create_order(param)
        else:
            return orders

    log.debug(f"Orders created: {orders}")

    return orders


async def process_telegram_message(
    update: Update, _: ContextTypes.DEFAULT_TYPE
) -> None:
    parser = MessageParser(update.message.text)

    if not parser.is_valid:
        log.debug(f"Message is not valid: {update.message.text}")
        return

    if parser.message_type == MessageType.GET_READY:
        orders = await process_get_ready(parser)

        if orders and orders[0].get("code", None) is None:
            await update.message.reply_text(
                f"Order created for #{orders[0]['symbol']}, "
                f"with entry {orders[0]['stopPrice']}"
            )
        else:
            await update.message.reply_text(
                f"Order fail for #{parser.symbol}"
                f"\ndetails: {json.dumps(orders, indent=4)}"
            )
    if parser.message_type == MessageType.OPENED:
        orders = await process_opened(parser)

        if orders and orders[0].get("code", None) is None:
            await update.message.reply_text(f"Order created for #{parser.symbol}")
        elif orders and orders[0].get("code", None) is not None:
            await update.message.reply_text(
                f"Order fail for #{parser.symbol}"
                f"\ndetails: {json.dumps(orders, indent=4)}"
            )
        else:
            log.info(f"Order ignored for #{parser.symbol}")
