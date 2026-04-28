import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import DISCOUNT_REDIRECT_URL
from bot.google_sheets import build_angry_payload, build_positive_payload, build_valentine_payload, send_to_sheets
from bot.keyboards import ReviewTypeCallback, main_menu_keyboard, cancel_menu_keyboard, review_type_keyboard
from bot.states import AngryReviewStates, PositiveReviewStates, ValentineStates

logger = logging.getLogger(__name__)
router = Router()


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _track_msg(state: FSMContext, *msg_ids: int) -> None:
    data = await state.get_data()
    tracked = data.get("_tracked", [])
    tracked.extend(msg_ids)
    await state.update_data(_tracked=tracked)


async def _cleanup(bot: Bot, chat_id: int, state: FSMContext) -> None:
    data = await state.get_data()
    for msg_id in data.get("_tracked", []):
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
    await state.clear()


async def _show_main_menu(target: Message, text: str) -> None:
    await target.answer(text, reply_markup=main_menu_keyboard())


# ─── /start ──────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot) -> None:
    await _cleanup(bot, message.chat.id, state)
    await _show_main_menu(message, "Привет! Нажмите кнопку ниже, чтобы оставить отзыв.")


# ─── Отмена (reply-кнопка) — регистрируется ДО FSM-хендлеров ─────────────────

@router.message(F.text == "Отмена")
async def btn_cancel_text(message: Message, state: FSMContext, bot: Bot) -> None:
    await _track_msg(state, message.message_id)
    await _cleanup(bot, message.chat.id, state)
    await _show_main_menu(message, "Сценарий отменён.")


# ─── /cancel ─────────────────────────────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, bot: Bot) -> None:
    current = await state.get_state()
    await _track_msg(state, message.message_id)
    await _cleanup(bot, message.chat.id, state)
    if current is None:
        await _show_main_menu(message, "Нет активного сценария.")
    else:
        await _show_main_menu(message, "Сценарий отменён.")


# ─── Главное меню ─────────────────────────────────────────────────────────────

@router.message(F.text == "Оставить отзыв")
async def btn_leave_review(message: Message, state: FSMContext) -> None:
    await state.clear()
    sent = await message.answer("Выберите тип обращения:", reply_markup=review_type_keyboard())
    await _track_msg(state, message.message_id, sent.message_id)


# ─── Inline "Отмена" ─────────────────────────────────────────────────────────

@router.callback_query(ReviewTypeCallback.filter(F.action == "cancel"))
async def cb_cancel(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer()
    await _cleanup(bot, callback.message.chat.id, state)
    await callback.message.answer("Сценарий отменён.", reply_markup=main_menu_keyboard())


# ─── Гневный отзыв ───────────────────────────────────────────────────────────

@router.callback_query(ReviewTypeCallback.filter(F.action == "angry_review"))
async def cb_angry_review(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AngryReviewStates.waiting_for_text)
    sent = await callback.message.answer(
        "Напишите ваш отзыв.",
        reply_markup=cancel_menu_keyboard(),
    )
    await _track_msg(state, sent.message_id)


@router.message(AngryReviewStates.waiting_for_text, F.text)
async def angry_review_text(message: Message, state: FSMContext, bot: Bot) -> None:
    await _track_msg(state, message.message_id)
    payload = build_angry_payload(message.from_user, message.text)
    await _cleanup(bot, message.chat.id, state)
    await send_to_sheets(payload)
    await message.answer("Спасибо, мы получили ваш отзыв.", reply_markup=main_menu_keyboard())


@router.message(AngryReviewStates.waiting_for_text)
async def angry_review_wrong(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")


# ─── Позитивный отзыв ────────────────────────────────────────────────────────

@router.callback_query(ReviewTypeCallback.filter(F.action == "positive_review"))
async def cb_positive_review(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(PositiveReviewStates.waiting_for_text)
    sent = await callback.message.answer(
        "Поделитесь тёплыми словами 😊",
        reply_markup=cancel_menu_keyboard(),
    )
    await _track_msg(state, sent.message_id)


@router.message(PositiveReviewStates.waiting_for_text, F.text)
async def positive_review_text(message: Message, state: FSMContext, bot: Bot) -> None:
    await _track_msg(state, message.message_id)
    payload = build_positive_payload(message.from_user, message.text)
    await _cleanup(bot, message.chat.id, state)
    await send_to_sheets(payload)
    await message.answer("Спасибо за тёплые слова!", reply_markup=main_menu_keyboard())


@router.message(PositiveReviewStates.waiting_for_text)
async def positive_review_wrong(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")


# ─── Валентинка ──────────────────────────────────────────────────────────────

@router.callback_query(ReviewTypeCallback.filter(F.action == "valentine"))
async def cb_valentine(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ValentineStates.waiting_for_barista_name)
    sent = await callback.message.answer(
        "Кому адресована валентинка?",
        reply_markup=cancel_menu_keyboard(),
    )
    await _track_msg(state, sent.message_id)


@router.message(ValentineStates.waiting_for_barista_name, F.text)
async def valentine_barista_name(message: Message, state: FSMContext) -> None:
    await _track_msg(state, message.message_id)
    await state.update_data(barista_name=message.text)
    await state.set_state(ValentineStates.waiting_for_cafe_address)
    sent = await message.answer("Укажите адрес кофейни в свободной форме:")
    await _track_msg(state, sent.message_id)


@router.message(ValentineStates.waiting_for_barista_name)
async def valentine_barista_name_wrong(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")


@router.message(ValentineStates.waiting_for_cafe_address, F.text)
async def valentine_cafe_address(message: Message, state: FSMContext) -> None:
    await _track_msg(state, message.message_id)
    await state.update_data(cafe_address=message.text)
    await state.set_state(ValentineStates.waiting_for_text)
    sent = await message.answer("Напишите текст валентинки:")
    await _track_msg(state, sent.message_id)


@router.message(ValentineStates.waiting_for_cafe_address)
async def valentine_cafe_address_wrong(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")


@router.message(ValentineStates.waiting_for_text, F.text)
async def valentine_text(message: Message, state: FSMContext, bot: Bot) -> None:
    await _track_msg(state, message.message_id)
    data = await state.get_data()
    payload = build_valentine_payload(
        message.from_user,
        data["barista_name"],
        data["cafe_address"],
        message.text,
    )
    await _cleanup(bot, message.chat.id, state)
    await send_to_sheets(payload)
    await message.answer("Валентинка отправлена 💌", reply_markup=main_menu_keyboard())


@router.message(ValentineStates.waiting_for_text)
async def valentine_text_wrong(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")


# ─── Скидка ──────────────────────────────────────────────────────────────────

@router.callback_query(ReviewTypeCallback.filter(F.action == "discount"))
async def cb_discount(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer()
    await _cleanup(bot, callback.message.chat.id, state)
    await callback.message.answer(
        f"Заберите скидку по ссылке: {DISCOUNT_REDIRECT_URL}",
        reply_markup=main_menu_keyboard(),
    )


# ─── Fallback ─────────────────────────────────────────────────────────────────

@router.message()
async def fallback(message: Message) -> None:
    await message.answer(
        "Не понимаю вас. Нажмите «Оставить отзыв» или используйте /start."
    )
