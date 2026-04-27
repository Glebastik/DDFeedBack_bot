from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


class ReviewTypeCallback(CallbackData, prefix="review"):
    action: str


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Оставить отзыв")]],
        resize_keyboard=True,
    )


def review_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="😡 Оставить гневный отзыв",
                callback_data=ReviewTypeCallback(action="angry_review").pack(),
            )],
            [InlineKeyboardButton(
                text="💌 Валентинка для бариста",
                callback_data=ReviewTypeCallback(action="valentine").pack(),
            )],
            [InlineKeyboardButton(
                text="😊 Оставить позитивный отзыв",
                callback_data=ReviewTypeCallback(action="positive_review").pack(),
            )],
            [InlineKeyboardButton(
                text="🎁 Хочу скидку в вашей сети",
                callback_data=ReviewTypeCallback(action="discount").pack(),
            )],
        ]
    )
