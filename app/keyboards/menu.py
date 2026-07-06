from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.buttons import append_back_button, append_close_button


def get_private_main_menu(chat_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Этот чат", callback_data=f"chat_menu:{chat_id}")],
            [InlineKeyboardButton(text="📢 Мои группы и каналы", callback_data="my_chats")],
            [InlineKeyboardButton(text="📖 Инструкция", callback_data="info")],
            [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )


def get_public_main_menu(chat_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Этот чат", callback_data=f"chat_menu:{chat_id}")],
            [InlineKeyboardButton(text="📢 Инструкция", callback_data="info")],
            [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )


def get_chat_menu(chat_id, bindings):
    if bindings:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Привязать VK-сообщество", callback_data=f"add_binding:{chat_id}")],
                [InlineKeyboardButton(text="📥 Перенести посты", callback_data=f"parse_menu:{chat_id}")],
                [InlineKeyboardButton(text="🗑️ Отвязать VK-сообщество", callback_data=f"del_binding_menu:{chat_id}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back:main_menu")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Привязать VK-сообщество", callback_data=f"add_binding:{chat_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back:main_menu")],
        ]
    )


def get_my_chats_menu(chats: list=None):
    chats = chats or []
    keyboard = []
    
    for c in chats:
        if c.chat_type == "channel":
            symbol = "📢"
        else:
            symbol = "💬"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{symbol} {c.title}",
                callback_data=f"chat_menu:{c.chat_id}"
            )
        ])
    
    append_back_button(keyboard, "main_menu")
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_delete_menu(chat_id: int, bindings: list=None, back_button: bool=True):
    keyboard = []
    
    for b in bindings:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{b[1].name}",
                callback_data=f"del_binding:{chat_id}:{b[0].group_id}"
            )
        ])
        
    if back_button:
        append_back_button(keyboard, chat_id)
    else: 
        append_close_button(keyboard)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_parse_menu(chat_id: int, bindings: list=None, back_button: bool=True):
    keyboard = []
    
    for b in bindings:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{b[1].name}",
                callback_data=f"parse:{chat_id}:{b[0].group_id}"
            )
        ])
        
    if back_button:
        append_back_button(keyboard, chat_id)
    else: 
        append_close_button(keyboard)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_suggest_parse_menu(chat_id: int, vk_group_link: int):
    keyboard = []
    keyboard.append([
        InlineKeyboardButton(
            text="📥 Перенести посты", 
            callback_data=f"parse:{chat_id}:{vk_group_link}"
        )
    ])
    
    append_back_button(keyboard, "main_menu")
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)