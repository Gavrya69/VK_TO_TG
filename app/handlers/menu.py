from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить группу", callback_data="add_group")],
        [InlineKeyboardButton(text="🗑️ Удалить группу", callback_data="del_group")],
        [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info")]
    ])
    return keyboard


def get_delete_menu(subscriptions):
    keyboard = []
    
    for sub in subscriptions:
        keyboard.append([
            InlineKeyboardButton(
                text=f"Группа {sub.group_id}",
                callback_data=f"del_group:{sub.group_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="Назад", callback_data="main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")]
    ])
    return keyboard