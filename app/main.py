from threading import Thread

from telegram import Update
from service import setting as Setting
from handler import process_telegram_message
from service import renew_key, get_logger, renew_session
from telegram.ext import MessageHandler, ApplicationBuilder, filters

log = get_logger(__name__)


if __name__ == "__main__":
    session_thread = Thread(target=renew_session, daemon=True)
    session_thread.start()

    key_thread = Thread(target=renew_key, daemon=True)
    key_thread.start()

    app = ApplicationBuilder().token(Setting.TELEGRAM_TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters=filters.TEXT & ~filters.COMMAND,
            callback=process_telegram_message,
        )
    )

    app.run_polling(drop_pending_updates=True, allowed_updates=Update.MESSAGE)
