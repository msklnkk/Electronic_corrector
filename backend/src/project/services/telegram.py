import requests
from asyncio import get_running_loop

TG_BOT_TOKEN = "8503261519:AAEUmz4GDhXX8jcQch9GeVe7uSTizuQeyVc"
CHANNEL_USERNAME = "@electronic_corrector"

def _sync_is_subscribed(telegram_id: int) -> bool:
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/getChatMember"
    try:
        r = requests.get(url, params={"chat_id": CHANNEL_USERNAME, "user_id": telegram_id}, timeout=10)
        data = r.json()
        if data.get("ok"):
            status = data.get("result", {}).get("status")
            return status in {"member", "administrator ", "creator"}
    except:
        pass
    return False

async def is_user_subscribed(telegram_id: int) -> bool:
    loop = get_running_loop()
    return await loop.run_in_executor(None, _sync_is_subscribed, telegram_id)