from aiogram.fsm.state import StatesGroup, State

class GroupControl(StatesGroup):
    waiting_for_add = State()
    waiting_for_post_count = State()