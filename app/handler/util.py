from service import get_logger
from service import setting as Setting

log = get_logger(__name__)


async def is_user_not_authorized(user_id: int) -> bool:
    if user_id == Setting.TELEGRAM_OWNER_ID:
        return False
    log.warning(f"Unauthorized user {user_id} tried to access the bot")
    return True
