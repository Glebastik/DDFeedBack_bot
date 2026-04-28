from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove


class ReviewTypeCallback(CallbackData, prefix="review"):
    action: str


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
            [InlineKeyboardButton(
                text="🚫 Отмена",
                callback_data=ReviewTypeCallback(action="cancel").pack(),
            )],
        ]
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
