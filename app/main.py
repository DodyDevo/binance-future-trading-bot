from threading import Thread

from service import setting as Setting
from telegram import Update, BotCommand
from service import renew_key, get_logger, renew_session
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ApplicationBuilder,
    filters,
)
from handler import (
    set_trade,
    set_target,
    set_leverage,
    set_ignore_open_order,
    process_telegram_message,
)

log = get_logger(__name__)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        commands=[
            BotCommand(command="leverage", description="Set new leverage"),
            BotCommand(command="trade", description="Set new trade amount"),
            BotCommand(command="target", description="Set new targer"),
            BotCommand(command="ignore-open", description="Set ignore set order"),
        ]
    )


if __name__ == "__main__":
    session_thread = Thread(target=renew_session, daemon=True)
    session_thread.start()

    key_thread = Thread(target=renew_key, daemon=True)
    key_thread.start()

    app = (
        ApplicationBuilder()
        .token(Setting.TELEGRAM_TOKEN)
        .post_init(post_init=post_init)
        .build()
    )

    app.add_handler(
        CommandHandler(
            command="leverage",
            callback=set_leverage,
            filters=filters.User(user_id=Setting.TELEGRAM_OWNER_ID),
        )
    )

    app.add_handler(
        CommandHandler(
            command="trade",
            callback=set_trade,
            filters=filters.User(user_id=Setting.TELEGRAM_OWNER_ID),
        )
    )

    app.add_handler(
        CommandHandler(
            command="target",
            callback=set_target,
            filters=filters.User(user_id=Setting.TELEGRAM_OWNER_ID),
        )
    )

    app.add_handler(
        CommandHandler(
            command="ignore-open",
            callback=set_ignore_open_order,
            filters=filters.User(user_id=Setting.TELEGRAM_OWNER_ID),
        )
    )

    app.add_handler(
        MessageHandler(
            filters=filters.TEXT
            & ~filters.COMMAND
            & filters.User(user_id=Setting.TELEGRAM_OWNER_ID),
            callback=process_telegram_message,
        )
    )

    app.run_polling(drop_pending_updates=True, allowed_updates=Update.MESSAGE)
