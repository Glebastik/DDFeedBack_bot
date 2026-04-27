import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
GOOGLE_APPS_SCRIPT_URL: str = os.getenv("GOOGLE_APPS_SCRIPT_URL", "")
DISCOUNT_REDIRECT_URL: str = os.getenv(
    "DISCOUNT_REDIRECT_URL",
    "https://example.com/discount",
)
TIMEZONE: str = "Europe/Moscow"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env")

if not GOOGLE_APPS_SCRIPT_URL:
    raise ValueError("GOOGLE_APPS_SCRIPT_URL не задан в .env")
