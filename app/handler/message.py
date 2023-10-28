from telegram import Update
from service import get_logger
from telegram.ext import ContextTypes

from .util import is_user_not_authorized

logger = get_logger(__name__)


async def process_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    current_user = update.effective_user

    if await is_user_not_authorized(current_user.id):
        return

    await update.message.reply_text("Hello, I'm a bot!")
