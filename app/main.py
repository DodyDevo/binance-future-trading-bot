from service import setting as Setting
from telegram.ext import ApplicationBuilder

app = ApplicationBuilder().token(Setting.TELEGRAM_TOKEN).build()

app.run_polling(drop_pending_updates=True)
