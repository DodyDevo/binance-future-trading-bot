from telegram import Update
from service import get_logger
from telegram.ext import ContextTypes
from model import MessageType, MessageParser

from .util import truncate, get_symbol_info, is_user_not_authorized

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
    log.debug(f"Truncated entry: {parser.entry}")
    log.debug(f"Truncated target: {parser.target}")
    log.debug(f"Truncated stop: {parser.stop}")


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
