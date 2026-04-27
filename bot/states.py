from aiogram.fsm.state import State, StatesGroup


class AngryReviewStates(StatesGroup):
    waiting_for_text = State()


class PositiveReviewStates(StatesGroup):
    waiting_for_text = State()


class ValentineStates(StatesGroup):
    waiting_for_barista_name = State()
    waiting_for_cafe_address = State()
    waiting_for_text = State()
