import json
from datetime import datetime

from telegram import Update
from service import get_logger
from telegram.ext import ContextTypes
from model import MessageType, MessageParser
from service import setting as Setting  # noqa F401

from .util import truncate, allowable, get_symbol_info, is_user_not_authorized

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

    with open("database.json", "w+") as file:
        try:
            data = json.load(file)
        except json.decoder.JSONDecodeError:
            data = {}
        data[parser.symbol] = order_data
        json.dump(data, file, indent=4)

    log.debug(f"Order data saved: {order_data}")


async def process_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    current_user = update.effective_user

    if await is_user_not_authorized(current_user.id):
        return

    parser = MessageParser(update.message.text)

    if not parser.is_valid:
        log.debug(f"Message is not valid: {update.message.text}")
        return

    if parser.message_type == MessageType.GET_READY:
        await process_get_ready(parser)
