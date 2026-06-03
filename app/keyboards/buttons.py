from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_back_button(target: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back:{target}")]
        ]
    )

def get_close_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")]
    ])
    return keyboard


def append_back_button(keyboard: list, target: str):
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"back:{target}"
        )
    ])
    
def append_close_button(keyboard: list):
    keyboard.append([
        InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data=f"close"
        )
    ])

