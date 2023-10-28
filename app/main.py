from telegram import Update
from service import get_logger
from handler import process_message
from service import setting as Setting
from telegram.ext import MessageHandler, ApplicationBuilder, filters

log = get_logger(__name__)

app = ApplicationBuilder().token(Setting.TELEGRAM_TOKEN).build()

app.add_handler(
    MessageHandler(
        filters=filters.TEXT & ~filters.COMMAND,
        callback=process_message,
    )
)

app.run_polling(drop_pending_updates=True, allowed_updates=Update.MESSAGE)
