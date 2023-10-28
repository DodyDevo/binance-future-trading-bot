from telegram import Update
from service import get_logger
from model import MessageParser
from telegram.ext import ContextTypes

from .util import is_user_not_authorized

logger = get_logger(__name__)


async def process_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    current_user = update.effective_user

    if await is_user_not_authorized(current_user.id):
        return

    parser = MessageParser(update.message.text)

    if not parser.is_valid:
        logger.debug(f"Message is not valid: {update.message.text}")
        return

    await update.message.reply_text(
        f"Is valid: {parser.is_valid}"
        f"\nMessage type: {parser.message_type}"
        f"\nSymbol: {parser.symbol}"
        f"\nSide: {parser.side}"
        f"\nEntry: {parser.entry}"
        f"\nTarget: {parser.target}"
    )
