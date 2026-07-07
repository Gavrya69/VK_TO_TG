import asyncio
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from html import escape

from database import db
from services.vk.client import vk

from keyboards.menu import (
    get_private_main_menu,
    get_public_main_menu,
    get_chat_menu,
    get_my_chats_menu,
    get_delete_menu,
    get_suggest_parse_menu,
    get_parse_menu,
    get_confirm_binding_menu,
)

from keyboards.buttons import get_back_button, get_close_button

from handlers.states import GroupControl
from services.tg import sync_chat_admins, send_post, update_user_chats


router = Router()


@router.callback_query(F.data == "about")
async def info_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔄 <b>Автопостинг VK → Telegram </b>\n\n"
        
        "Бот предназначен для автоматического переноса публикаций из VK-сообществ "
        "вам, в ваши Telegram-чаты и каналы.\n\n"
        
        "📌 <b>Возможности:</b>\n"
        "• Автоматический парсинг новых постов из VK\n"
        "• Отправка текста, фото и видео в Telegram\n"
        "• Поддержка нескольких привязанных групп\n"
        "• Разделение постов на части при больших текстах\n"
        "• Ручной просмотр постов и закреплённых записей из любых открытых групп\n"
        "• Настройка привязок VK → Telegram",     
        reply_markup=get_back_button("main_menu"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "info")
async def info_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔄 <b>Инструкция по использованию бота</b>\n\n"
        
        "━━━━━━━━━━━━━━━\n"
        "👥 <b>Добавление бота</b>\n\n"
        "• Добавьте бота в чат или канал\n"
        "• Для каналов <b>обязательно</b> выдайте права администратора\n"
        "• Бот автоматически привяжет администраторов к каналу\n"
        "• Администраторы чата автоматически получают доступ к привязке и управлению группами\n\n"
        
        "━━━━━━━━━━━━━━━\n"
        "🔗 <b>Как привязать VK-группу</b>\n\n"
        "1. Открой чат или канал, куда добавлен бот\n"
        "2. Нажми Привязать VK-группу\n"
        "3. Отправь ссылку на VK-группу или её короткое имя:\n"
        "   <code>https://vk.com/public123456</code>\n"
        "   <code>public123456</code>\n"
        "4. Дождись подтверждения привязки\n\n"
        
        "━━━━━━━━━━━━━━━\n"
        "📥 <b>Как переносятся посты</b>\n\n"
        "• Новые посты отправляются автоматически спустя несколько минут после публикации\n"
        "• Поддерживаются фото и видео (видео размером до 50 мб)\n"
        "• Длинные тексты разбиваются на части\n"
        "• Закреплённые посты обрабатываются отдельно\n"
        "• Перенос постов, помеченных как реклама, выключен по-умолчанию\n\n"
        
        "━━━━━━━━━━━━━━━\n"
        "⚙️ <b>Основные команды</b>\n"
        "/start — главное меню\n"
        "/about — информация о боте\n"
        "/info — эта инструкция\n"
        "/get_posts — ручной просмотр постов\n"
        "/get_pinned — закреплённые посты\n\n"
        
        "━━━━━━━━━━━━━━━\n"
        "⚠️ <b>Важно</b>\n"
        "• Бот работает только с открытыми VK-группами\n"
        "• Настройки бота меняются <b>в зависимости от чата</b>\n"
        "  - В <b>личных сообщениях</b> доступно управление всеми привязками (все чаты и каналы пользователя)\n"
        "  - В <b>группах</b> бот управляет только этой конкретной группой (локальные настройки)\n"
        "  - В <b>каналах</b> диалог с ботом невозможен — управление выполняется только через личные сообщения\n"
        "• При изменении прав бота может потребоваться повторная настройка\n",
        
        reply_markup=get_back_button("main_menu"),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    chat_id = callback.message.chat.id
    
    if callback.message.chat.type == "private":
        markup = get_private_main_menu(chat_id)
    else:
        markup = get_public_main_menu(chat_id)
        
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>",
        reply_markup=markup,
        parse_mode="HTML",
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("back:"))
async def back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    target = callback.data.split(":", 1)[1]
    
    if target == "main_menu":
        await main_menu(callback, state)
    else :
        await chat_menu(callback, state)
    
    await callback.answer()


@router.callback_query(F.data == "close")
async def close(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    await callback.message.delete()
    
    await callback.answer()


@router.callback_query(F.data.startswith("chat_menu:"))
async def chat_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    chat_id = int(callback.data.split(":")[1])
    
    async with db.SessionLocal() as session:
        bindings = await db.get_bindings_with_groups(
            session=session,
            chat_id=chat_id,
        )
        
        chat = await db.get_chat(session, chat_id)
        
        if chat.chat_type == "private":
            header = "⚙️ <b>Настройки этого чата</b>\n"
        else:
            chat_type_names = {
                "channel": "канала",
                "group": "группы",
                "supergroup": "группы",
            }
            chat_type = chat_type_names.get(chat.chat_type, "чата")
            
            header = f"⚙️ <b>Настройки {chat_type} «{chat.title}»</b>\n"
        
        if bindings:
            lines = [header, "🔗 <i>Привязанные VK-сообщества:</i>"]
            for i, (_, group) in enumerate(bindings, start=1):
                lines.append(
                    f'{i}. <a href="https://vk.com/{group.screen_name}">'
                    f'{escape(group.name)}</a>'
                )
            text = "\n".join(lines)
        else:
            text = f"{header}\nℹ️ Пока <i>не привязано</i> ни одно VK-сообщество."
    
    await callback.message.edit_text(
        text,
        reply_markup=get_chat_menu(chat_id, bindings),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    
    await callback.answer()


@router.callback_query(F.data == "my_chats")
async def my_chats_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    
    async with db.SessionLocal() as session:
        chats_by_admin = await db.get_chats_by_admin(
            session=session,
            user_id=user_id,
        )
        
        chat_ids = [c.chat_id for c in chats_by_admin]
        
        chats = await db.get_chats(
            session=session,
            chat_ids=chat_ids
        )
        
        await update_user_chats(
            bot=callback.bot,
            session=session,
            db_chats=chats
        )
        
    if chats:
        await callback.message.edit_text(
            f"<b>Ваши подключенные каналы (📢) и группы (💬):</b>",
            reply_markup=get_my_chats_menu(chats),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    else:
        await callback.message.edit_text(
            "ℹ️ Вы пока <i>не добавляли</i> бота в каналы и группы.",
            reply_markup=get_my_chats_menu(chats),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("add_binding:"))
async def add_binding_menu(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    
    await state.set_state(GroupControl.waiting_for_add)
    await state.update_data(target_chat_id=chat_id)
    
    await callback.message.edit_text(
        "Отправьте ссылку, ID или короткий адрес VK-группы.\n"
        '(например, <i>"https://vk.com/club123"</i> или <i>"club123"</i>)',
        reply_markup=get_back_button(chat_id),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    
    await callback.answer()


@router.message(GroupControl.waiting_for_add)
async def process_binding(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data["target_chat_id"]
    link = message.text
    
    result = (await vk.get_group_info(link))
    
    if not result["ok"]:
        status = result.get("status", "unknown_error")
        
        group = result.get("group")
        
        if group:
            group_link = f'<a href="https://vk.com/{group.screen_name}">{group.name}</a>'
        else:
            group_link = ""
        
        if status == "not_found":
            await message.answer(
                "🔍 <b>Группа не найдена.</b>"
                "Проверьте правильность введенной ссылки или ID.",
                reply_markup=get_back_button(chat_id),
                parse_mode="HTML",
            )
        elif status == "access_denied":
            await message.answer(
                "🚫 <b>Ошибка доступа.</b>\n"
                "Перепроверьте токен доступа VK.",
                reply_markup=get_back_button(chat_id),
                parse_mode="HTML",
            )
        elif status == "private":
            await message.answer(
                "🔒 <b>Доступ ограничен</b>\n"
                f"Сообщество {group_link} является приватным.",
                reply_markup=get_back_button(chat_id),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        elif status == "closed":
            await message.answer(
                "🔒 <b>Доступ ограничен</b>\n"
                f"Сообщество {group_link} является закрытым.",
                reply_markup=get_back_button(chat_id),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        elif status == "network_error":
            await message.answer(
                "🌐 <b>Ошибка сети.</b>\n"
                "Проверьте подключение и попробуйте снова.",
                reply_markup=get_back_button(chat_id),
                parse_mode="HTML",
            )
        elif status == "timeout":
            await message.answer(
                "⏳ <b>Таймаут запроса.</b>\n"
                "VK не ответил вовремя, попробуйте ещё раз.",
                reply_markup=get_back_button(chat_id),
                parse_mode="HTML",
            )
        elif status == "too_many_requests":
            await message.answer(
                "⚠️ <b>Слишком много запросов.</b>\n"
                "Попробуйте через несколько секунд.",
                reply_markup=get_back_button(chat_id),
                parse_mode="HTML",
            )
        elif status == "unknown_error":
            await message.answer(
                "⚠️ <b>Неизвестная ошибка.</b>\n"
                "Что-то пошло не так.",
                reply_markup=get_back_button(chat_id),
                parse_mode="HTML",
            )
        
        await state.clear()
        return
    
    group = result["group"]
    
    await message.answer(
        f"🔍 Вы желаете привязать группу "
        f'<i><a href="https://vk.com/{group.screen_name}">{group.name}</a></i>?',
        reply_markup=get_confirm_binding_menu(message.chat.id, group.id, True),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    
    await state.clear()


@router.callback_query(F.data.startswith("process_binding:"))
async def confirm_binding(callback: CallbackQuery):    
    chat_id = int(callback.data.split(":")[1])
    group_id = int(callback.data.split(":")[2])
    back_button = bool(int(callback.data.split(":")[3]))
    
    group = (await vk.get_group_info(group_id))["group"]
    
    posts = (await vk.get_group_posts(group_id))["posts"]
    last_post_id = posts[0].id if posts else 0
    
    async with db.SessionLocal() as session:
        result = await db.create_binding(
            session=session,
            chat_id=chat_id,
            chat_title=(
                callback.message.chat.username 
                if callback.message.chat.type == "private" 
                else callback.message.chat.title
            ),
            chat_type=callback.message.chat.type,
            group=group,
            last_post_id=last_post_id
            )
        
    if result["created"]:
        await callback.message.edit_text(
            f'✅ Группа <i><a href="https://vk.com/{group.screen_name}">{group.name}</a></i> успешно привязана.\n'
            f"Желаете перенести посты?",
            reply_markup=get_suggest_parse_menu(chat_id, group.id, back_button),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    else:
        await callback.message.edit_text(
            f'ℹ️ Группа <i><a href="https://vk.com/{group.screen_name}">{group.name}</a></i> уже привязана.',
            reply_markup = (
                get_back_button(chat_id)
                if back_button
                else get_close_button()
            ),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )


@router.callback_query(F.data.startswith("parse_menu:"))
async def parse_posts_menu(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    
    async with db.SessionLocal() as session:
        bindings = await db.get_bindings_with_groups(
            session=session,
            chat_id=chat_id,
        )
        
    if bindings:
        await callback.message.edit_text(
            "📥 С какой группы хотите перенести посты?",
            reply_markup=get_parse_menu(chat_id, bindings)
        )
    else:
        await callback.answer("ℹ️ Сюда пока <i>не привязано</i> ни одно VK-сообщество.")
    
    await callback.answer()


@router.callback_query(F.data.startswith("parse:"))
async def parse_posts(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    group_id = int(callback.data.split(":")[2])
    
    await state.set_state(GroupControl.waiting_for_post_count)
    await state.update_data(target_chat_id=chat_id)
    await state.update_data(group_id=group_id)
    
    await callback.message.edit_text(
        "🔢 Сколько постов вы хотите перенести?",
        reply_markup=get_back_button(chat_id)
    )
    
    await callback.answer()


@router.message(GroupControl.waiting_for_post_count)
async def process_parsing(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data["target_chat_id"]
    group_id = data["group_id"]
    
    try:
        posts_count = int(message.text)
    except:
        await message.answer(
            "❌ <b>Ошибка ввода.</b>\n"
            "Необходимо ввести корректное число.",
            reply_markup=get_back_button(chat_id),
            parse_mode="HTML"
        )
        return
    
    if not 0 < posts_count <= 100:
        await message.answer(
            "⚠️ Пожалуйста, введите число <i>от 1 до 100</i>.",
            reply_markup=get_back_button(chat_id),
            parse_mode="HTML"
        )
        return
    
    loading_msg = await message.answer(
        "⏳ <i>Подождите, начинаю переносить посты...</i>",
        parse_mode="HTML"
    )
    
    result = await vk.get_group_posts(group_id, posts_count)
    
    if result["ok"]:
        posts = result["posts"]
        posts.reverse()
        
        if not posts:        
            await loading_msg.edit_text(
                "🔍 <b>Посты не найдены.</b>"
                "В данной группе отсутствуют публикации.",
                reply_markup=get_back_button("main_menu"),
                parse_mode="HTML"
            )
            return
        
        for post in posts: 
            await send_post(
                bot=message.bot,
                chat_id=chat_id,
                post=post
            )
        
        await loading_msg.delete()
        
        await message.answer(
            "✅ <b>Готово.</b>\n"
            "Посты были успешно отправлены.",
            reply_markup=get_close_button(),
            parse_mode="HTML"
        )
        
    else:
        await loading_msg.edit_text(
            "⚠️ <b>Ошибка.</b>\n"
            f"{result['status']}",
            reply_markup=get_close_button(),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("del_binding_menu:"))
async def del_binding_menu(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    
    async with db.SessionLocal() as session:
        bindings = await db.get_bindings_with_groups(
            session=session,
            chat_id=chat_id,
        )
        
    if bindings:
        await callback.message.edit_text(
            "🗑️ Какую VK-группу хотите отвязать?",
            reply_markup=get_delete_menu(chat_id, bindings),
            parse_mode="HTML"
        )
    else:
        await callback.answer(
            "ℹ️ Сюда пока <i>не привязана</i> на одна VK-группа.",
            parse_mode="HTML",
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("del_binding:"))
async def process_binding(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    group_id = int(callback.data.split(":")[2])
    
    async with db.SessionLocal() as session:
        await db.delete_binding(
            session=session,
            group_id=group_id,
            chat_id=chat_id,
        )
        bindings = await db.get_bindings_with_groups(
            session=session,
            chat_id=chat_id,
        )
    
    if bindings:
        await callback.message.edit_text(
            "🗑️ Какую VK-группу хотите отвязать?",
            reply_markup=get_delete_menu(chat_id, bindings),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "ℹ️ Сюда пока <i>не привязана</i> на одна VK-группа.",
            reply_markup=get_delete_menu(chat_id, bindings),
            parse_mode="HTML"
        )
    
    await callback.answer("✅ Удалено.")


@router.my_chat_member()
async def on_bot_added(event: ChatMemberUpdated, bot):
    chat_id = event.chat.id
    
    async with db.SessionLocal() as session:
        chat = await db.get_chat(session, chat_id)
        
        if not chat:
            chat = await db.add_chat(
                session=session,
                chat_id=chat_id,
                title=event.chat.title or "unknown",
                chat_type=event.chat.type,
            )
        
        new = event.new_chat_member.status
        
        if new in ("member", "administrator"):
            await asyncio.sleep(2) # for sync
            await sync_chat_admins(
                bot=bot,
                session=session,
                chat_id=chat_id,
            )
        elif new in ("left", "kicked"):
            await asyncio.sleep(2) # for sync
            await db.delete_chat(
                session=session,
                chat_id=chat_id,
            )
