import json
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
    check_balance,
    get_symbol_info,
    set_margin_type,
    auto_cancel_order,
    is_user_not_authorized,
)

log = get_logger(__name__)


async def process_get_ready(parser: MessageParser) -> None:
    symbol_info = await get_symbol_info(parser.symbol)

    price_precision = symbol_info.get("pricePrecision", None)

    if not price_precision:
        log.error(f"Price precision not found for symbol: {parser.symbol}")
        return

    parser.entry = await truncate(parser.entry, price_precision)
    parser.target = await truncate(parser.target, price_precision)
    parser.stop = await truncate(parser.stop, price_precision)

    quantity, leverage = await allowable(parser.symbol, parser.entry)
    quantity = await truncate(quantity, symbol_info.get("quantityPrecision", None))

    order_data = {
        "entry": parser.entry,
        "target": parser.target,
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

    log.debug(f"Order data saved: {order_data}")


async def process_opened(parser: MessageParser) -> dict | None:
    balance = await check_balance()

    if balance < Setting.TRADE_AMOUNT:
        log.error(
            f"Stop trading balance is less than {Setting.TRADE_AMOUNT}, "
            "current balance {balance}"
        )
        return None

    with open("database.json", "r") as file:
        data = json.load(file)

    order_data = data.get(parser.symbol, None)

    if not order_data:
        log.error(f"Order data not found for symbol: {parser.symbol}")
        return None

    now = int(datetime.now().timestamp())
    diffrence = now - order_data["timestamp"]

    if diffrence > timedelta(hours=4).total_seconds():
        log.error(f"Order data is expired for symbol: {parser.symbol}")
        return None

    await set_margin_type(margin_type="CROSSED", symbol=parser.symbol)

    param = [
        {
            "symbol": parser.symbol,
            "side": order_data["side"],
            "type": "MARKET",
            "quantity": str(order_data["quantity"]),
            "workingType": "MARK_PRICE",
            "recvWindow": str(Setting.BINANCE_TIMEOUT),
        },
    ]

    order_created = create_order(param)
    await auto_cancel_order(parser.symbol)

    return order_created


async def process_telegram_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    current_user = update.effective_user

    if await is_user_not_authorized(current_user.id):
        return

    parser = MessageParser(update.message.text)

    if not parser.is_valid:
        log.debug(f"Message is not valid: {update.message.text}")
        return

    if parser.message_type == MessageType.GET_READY:
        await process_get_ready(parser)
    elif parser.message_type == MessageType.OPENED:
        order = await process_opened(parser)
        if order:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=json.dumps(order, indent=4),
            )
