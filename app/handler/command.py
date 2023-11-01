from telegram import Update
from service import get_logger
from telegram.ext import ContextTypes
from service import setting as Setting

log = get_logger(__name__)


async def set_leverage(update: Update, _: ContextTypes) -> None:
    _, variable = update.message.text.split(maxsplit=1)
    try:
        Setting.LEVERAGE = int(variable)
        await update.message.reply_text(f"LEVERAGE set to {Setting.LEVERAGE}")
    except ValueError:
        await update.message.reply_text("Invalid value for LEVERAGE")


async def set_trade(update: Update, _: ContextTypes) -> None:
    _, variable = update.message.text.split(maxsplit=1)
    try:
        Setting.TRADE_AMOUNT = float(variable)
        await update.message.reply_text(f"TRADE AMOUNT set to {Setting.TRADE_AMOUNT}")
    except ValueError:
        await update.message.reply_text("Invalid value for TRADE AMOUNT")


async def set_target(update: Update, _: ContextTypes) -> None:
    _, variable = update.message.text.split(maxsplit=1)
    try:
        Setting.TARGET = int(variable)
        await update.message.reply_text(f"TARGET set to {Setting.TARGET}")
    except ValueError:
        await update.message.reply_text("Invalid value for TARGET")
