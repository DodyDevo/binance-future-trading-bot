from service import get_logger
from service import setting as Setting
from telegram.ext import ApplicationBuilder

log = get_logger(__name__)

app = ApplicationBuilder().token(Setting.TELEGRAM_TOKEN).build()

app.run_polling(drop_pending_updates=True)
