from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Этот чат", callback_data="my_group")],
        [InlineKeyboardButton(text="📋 Группы и каналы", callback_data="del_group")],
        [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")]
    ])
    return keyboard


def get_delete_menu(bindings: list=[], menu_button: bool=True):
    keyboard = []
    
    if menu_button:
        for b in bindings:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"VK {b.vk_group_id}",
                    callback_data=f"del_group_menu:{b.vk_group_id}"
                )
            ])
        keyboard.append([
            InlineKeyboardButton(
                text="Назад",
                callback_data="main_menu"
            )
        ])
    else:
        for b in bindings:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"VK {b.vk_group_id}",
                    callback_data=f"del_group_chat:{b.vk_group_id}"
                )
            ])
        keyboard.append([
            InlineKeyboardButton(
                text="Закрыть",
                callback_data="close"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")]
    ])
    return keyboard


def get_close_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Закрыть", callback_data="close")]
    ])
    return keyboard