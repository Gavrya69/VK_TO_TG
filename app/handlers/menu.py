from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_private_main_menu(chat_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Этот чат", callback_data=f"chat_menu:{chat_id}")],
            [InlineKeyboardButton(text="📋 Группы и каналы", callback_data="my_chats")],
            [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )

def get_public_main_menu(chat_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Этот чат", callback_data=f"chat_menu:{chat_id}")],
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

def get_chat_menu(chat_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить VK группу", callback_data=f"add_binding:{chat_id}")],
            [InlineKeyboardButton(text="🗑️ Удалить VK группу", callback_data=f"del_binding_menu:{chat_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back:main_menu")],
        ]
    )


def get_my_chats_menu(chats: list=[]):
    keyboard = []
    for c in chats:
        keyboard.append([
            InlineKeyboardButton(
                text=f"TG {c.title}",
                callback_data=f"chat_menu:{c.telegram_chat_id}"
            )
        ])
        
    append_back_button(keyboard, "main_menu")
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)







def get_delete_menu(chat_id: int, bindings: list = [], back_button: bool=True):
    keyboard = []
    
    for b in bindings:
        keyboard.append([
            InlineKeyboardButton(
                text=f"VK {b.vk_group_id}",
                callback_data=f"del_binding:{chat_id}:{b.vk_group_id}"
            )
        ])
        
    if back_button:
        append_back_button(keyboard, chat_id)
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

