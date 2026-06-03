from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_private_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Этот чат", callback_data="this_chat")],
            [InlineKeyboardButton(text="📋 Группы и каналы", callback_data="my_chats")],
            [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )

def get_chat_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Этот чат", callback_data="this_chat")],
            [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )

def get_back_button(target: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back:{target}")]
        ]
    )

def get_this_chat_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить VK группу", callback_data="add_group")],
            [InlineKeyboardButton(text="🗑️ Удалить VK группу", callback_data="del_group")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back:main_menu")],
        ]
    )


def get_my_chats_menu(chats: list=[]):
    keyboard = []
    
    for c in chats:
        keyboard.append([
            InlineKeyboardButton(
                text=f"TG {c.title}",
                callback_data=f"settings:{c.telegram_chat_id}"
            )
        ])
        
    append_back_button(keyboard, "main_menu")
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)







def get_delete_menu(bindings: list=[], back_button: bool=True):
    keyboard = []
    
    for b in bindings:
        keyboard.append([
            InlineKeyboardButton(
                text=f"VK {b.vk_group_id}",
                callback_data=f"del_group_menu:{b.vk_group_id}"
            )
        ])
        
    if back_button:
        append_back_button(keyboard, "this_chat")
    else: 
        append_close_button(keyboard)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)




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

