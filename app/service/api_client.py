from service import setting as Setting
from binance.um_futures import UMFutures

api_client = UMFutures(
    key=Setting.BINANCE_API_KEY,
    secret=Setting.BINANCE_API_SECRET,
    base_url=Setting.BINANCE_BASE_URL,
)
