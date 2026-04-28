import logging

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import DISCOUNT_REDIRECT_URL
from bot.google_sheets import build_angry_payload, build_positive_payload, build_valentine_payload, send_to_sheets
from bot.keyboards import ReviewTypeCallback, welcome_keyboard, review_type_keyboard, remove_keyboard
from bot.states import AngryReviewStates, PositiveReviewStates, ValentineStates

logger = logging.getLogger(__name__)
router = Router()

WELCOME_TEXT = (
    "☕ <b>Добро пожаловать!</b>\n\n"
    "Здесь вы можете оставить отзыв о нашей кофейне, "
    "написать валентинку бариста или получить скидку.\n\n"
    "Нажмите кнопку ниже, чтобы начать."
)


async def _send_welcome(target: Message) -> None:
    await target.answer(WELCOME_TEXT, reply_markup=welcome_keyboard())


# ─── /start ──────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    tmp = await message.answer(".", reply_markup=remove_keyboard())
    await tmp.delete()
    await _send_welcome(message)


# ─── /cancel ─────────────────────────────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    if current is not None:
        await message.answer("Сценарий отменён.")
    await _send_welcome(message)


# ─── Кнопка "Оставить отзыв" (inline) ───────────────────────────────────────

@router.callback_query(ReviewTypeCallback.filter(F.action == "open_menu"))
async def cb_open_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer("Выберите тип обращения:", reply_markup=review_type_keyboard())


# ─── Inline "Отмена" ─────────────────────────────────────────────────────────

@router.callback_query(ReviewTypeCallback.filter(F.action == "cancel"))
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer("Сценарий отменён.")
    await _send_welcome(callback.message)


# ─── Гневный отзыв ───────────────────────────────────────────────────────────

@router.callback_query(ReviewTypeCallback.filter(F.action == "angry_review"))
async def cb_angry_review(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AngryReviewStates.waiting_for_text)
    await callback.message.answer(
        "Напишите ваш отзыв в формате: адрес, время, текст отзыва."
    )


@router.message(AngryReviewStates.waiting_for_text, F.text)
async def angry_review_text(message: Message, state: FSMContext) -> None:
    payload = build_angry_payload(message.from_user, message.text)
    await state.clear()
    await send_to_sheets(payload)
    await message.answer("Спасибо, мы получили ваш отзыв. 🙏")
    await _send_welcome(message)


@router.message(AngryReviewStates.waiting_for_text)
async def angry_review_wrong(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")


# ─── Позитивный отзыв ────────────────────────────────────────────────────────

@router.callback_query(ReviewTypeCallback.filter(F.action == "positive_review"))
async def cb_positive_review(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(PositiveReviewStates.waiting_for_text)
    await callback.message.answer(
        "Поделитесь тёплыми словами 😊\nФормат: адрес, время, текст отзыва."
    )


@router.message(PositiveReviewStates.waiting_for_text, F.text)
async def positive_review_text(message: Message, state: FSMContext) -> None:
    payload = build_positive_payload(message.from_user, message.text)
    await state.clear()
    await send_to_sheets(payload)
    await message.answer("Спасибо за тёплые слова! ❤️")
    await _send_welcome(message)


@router.message(PositiveReviewStates.waiting_for_text)
async def positive_review_wrong(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")


# ─── Валентинка ──────────────────────────────────────────────────────────────

@router.callback_query(ReviewTypeCallback.filter(F.action == "valentine"))
async def cb_valentine(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ValentineStates.waiting_for_barista_name)
    await callback.message.answer("Кому адресована валентинка?")


@router.message(ValentineStates.waiting_for_barista_name, F.text)
async def valentine_barista_name(message: Message, state: FSMContext) -> None:
    await state.update_data(barista_name=message.text)
    await state.set_state(ValentineStates.waiting_for_cafe_address)
    await message.answer("Укажите адрес кофейни в свободной форме:")


@router.message(ValentineStates.waiting_for_barista_name)
async def valentine_barista_name_wrong(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")


@router.message(ValentineStates.waiting_for_cafe_address, F.text)
async def valentine_cafe_address(message: Message, state: FSMContext) -> None:
    await state.update_data(cafe_address=message.text)
    await state.set_state(ValentineStates.waiting_for_text)
    await message.answer("Напишите текст валентинки:")


@router.message(ValentineStates.waiting_for_cafe_address)
async def valentine_cafe_address_wrong(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")


@router.message(ValentineStates.waiting_for_text, F.text)
async def valentine_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    payload = build_valentine_payload(
        message.from_user,
        data["barista_name"],
        data["cafe_address"],
        message.text,
    )
    await state.clear()
    await send_to_sheets(payload)
    await message.answer("Валентинка отправлена 💌")
    await _send_welcome(message)


@router.message(ValentineStates.waiting_for_text)
async def valentine_text_wrong(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")


# ─── Скидка ──────────────────────────────────────────────────────────────────

@router.callback_query(ReviewTypeCallback.filter(F.action == "discount"))
async def cb_discount(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(f"Заберите скидку по ссылке: {DISCOUNT_REDIRECT_URL}")
    await _send_welcome(callback.message)


# ─── Fallback ─────────────────────────────────────────────────────────────────

@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Используйте /start для начала работы с ботом.")
