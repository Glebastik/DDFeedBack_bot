import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import aiohttp

from bot.config import GOOGLE_APPS_SCRIPT_URL, TIMEZONE

logger = logging.getLogger(__name__)

SHEET_MAP = {
    "angry_review": "Гневные отзывы",
    "positive_review": "Позитивные отзывы",
    "valentine": "Валентинки",
}


def _now_str() -> str:
    tz = ZoneInfo(TIMEZONE)
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


def build_angry_payload(user, text: str) -> dict:
    return {
        "type": "angry_review",
        "sheet_name": SHEET_MAP["angry_review"],
        "text": text,
        "username": user.username or "",
        "user_id": user.id,
        "full_name": user.full_name,
        "created_at": _now_str(),
    }


def build_positive_payload(user, text: str) -> dict:
    return {
        "type": "positive_review",
        "sheet_name": SHEET_MAP["positive_review"],
        "text": text,
        "username": user.username or "",
        "user_id": user.id,
        "full_name": user.full_name,
        "created_at": _now_str(),
    }


def build_valentine_payload(user, barista_name: str, cafe_address: str, text: str) -> dict:
    return {
        "type": "valentine",
        "sheet_name": SHEET_MAP["valentine"],
        "barista_name": barista_name,
        "cafe_address": cafe_address,
        "text": text,
        "username": user.username or "",
        "user_id": user.id,
        "full_name": user.full_name,
        "created_at": _now_str(),
    }


async def send_to_sheets(payload: dict) -> None:
    logger.info("Отправка в Apps Script: type=%s user_id=%s", payload.get("type"), payload.get("user_id"))
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GOOGLE_APPS_SCRIPT_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status in (200, 201, 302):
                    logger.info("Данные успешно отправлены в Google Sheets")
                else:
                    response_text = await resp.text()
                    logger.error(
                        "Apps Script вернул неожиданный статус %s: %s",
                        resp.status,
                        response_text,
                    )
    except aiohttp.ClientError as exc:
        logger.error("Ошибка соединения с Apps Script: %s", exc)
    except Exception as exc:
        logger.exception("Неожиданная ошибка при отправке в Apps Script: %s", exc)
