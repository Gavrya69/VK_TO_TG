import re

from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message

from database import db
from services.vk.client import vk

from keyboards.menu import get_private_main_menu, get_public_main_menu, get_confirm_binding_menu
from keyboards.buttons import get_close_button

from services.tg import send_post


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    chat_id = message.chat.id
    
    async with db.SessionLocal() as session:
        chat = await db.get_chat(session, chat_id)
        if not chat:
            chat = await db.add_chat(
                session=session,
                chat_id=chat_id,
                title=(
                    message.chat.username 
                    if message.chat.type == "private" 
                    else message.chat.title
                ),
                chat_type=message.chat.type,
            )
    
    if message.chat.type == "private":
        markup = get_private_main_menu(chat_id)
    else:
        markup = get_public_main_menu(chat_id)
    
    await message.answer(
        "<b>🏠 Главное меню:</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )


@router.message(Command("about"))
async def cmd_about(message: Message):
    await message.answer(
        "🔄 <b>Автопостинг из VK в Telegram</b>\n\n"
        "Данный бот занимается переносом публикаций из сообществ ВКонтакте в ваши Telegram-каналы и чаты.",
        reply_markup=get_close_button(),
        parse_mode="HTML",
    )


@router.message(Command("info"))
async def cmd_info(message: Message):
    await message.answer(
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
        "• При изменении прав бота может потребоваться повторная настройка\n",
        
        reply_markup=get_close_button(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Список команд:</b>\n\n"
        "/help - список команд\n"
        "/start - меню бота\n"
        "/about - информация о боте\n",
        parse_mode="HTML"
    )


@router.message(Command("get_posts"))
async def cmd_get_posts(message: Message):
    args = message.text.split(maxsplit=2)
    try:
        link = args[1]
        count = int(args[2])
    except (IndexError, ValueError):
        await message.answer(
            "<b>⚠️ Использование команды:</b>\n"
            "<code>/get_posts [ссылка на группу] [количество постов]</code>",
            reply_markup=get_close_button(),
            parse_mode="HTML"
            )
        return
    
    loading_msg = await message.answer(
        "⏳ <i>Подождите, начинаю переносить посты...</i>",
        parse_mode="HTML"
    )
    
    count = max(1, min(count, 50))
    result = await vk.get_group_posts(link, count)
    
    if result["ok"]:
        posts = result["posts"]
        
        if not posts:        
            await loading_msg.edit_text(
                "🔍 <b>Посты не найдены.</b>"
                "В данной группе отсутствуют публикации.",
                reply_markup=get_close_button(),
                parse_mode="HTML"
            )
            return
        
        for post in posts:
            await send_post(
                bot=message.bot,
                chat_id=message.chat.id,
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
            parse_mode="HTML"
        )


@router.message(Command("get_pinned"))
async def cmd_get_pinned(message: Message):
    args = message.text.split(maxsplit=2)
    if len(args) <= 1:
        await message.answer(
            "<b>⚠️ Использование команды:</b>\n"
            "<code>/get_pinned [ссылка на группу]</code>",
            reply_markup=get_close_button(),
            parse_mode="HTML"
            )
        return
    
    loading_msg = await message.answer(
        "⏳ <i>Подождите, начинаю переносить посты...</i>",
        parse_mode="HTML"
    )
    
    link = args[1]    
    result = await vk.get_group_posts(link, 5, with_pinned=True)
    
    if result["ok"]:
        posts = result["posts"]
        pinned_posts = [post for post in posts if post.is_pinned]
        
        if not pinned_posts:        
            await loading_msg.edit_text(
                "🔍 <b>Посты не найдены.</b>"
                "В данной группе отсутствуют публикации.",
                reply_markup=get_close_button(),
                parse_mode="HTML"
            )
            return
        
        for post in pinned_posts:
            await send_post(
                bot=message.bot,
                chat_id=message.chat.id,
                post=post
            )
        
        await loading_msg.delete()
        
        await message.answer(
            "✅ <b>Готово.</b>\n"
            "Посты были успешно отправлены.",
            reply_markup=get_close_button("main_menu"),
            parse_mode="HTML"
        )
    else:
        await loading_msg.edit_text(
            "⚠️ <b>Ошибка.</b>\n"
            f"{result['status']}",
            reply_markup=get_close_button("main_menu"),
            parse_mode="HTML"
        )


@router.message(Command("asd"))
async def cmd_some_command(message: Message):
    args = message.text.split(maxsplit=1)
    
    loading_msg = await message.answer(
        "⏳ Подождите, начинаю работу...\nЭто сообщение удалится при завершении."
    )
    
    link = args[1]
    
    import json
    from utils import extract_group_ref
    
    i = 0
    
    i += 1
    response = await vk.request("groups.getById", {
            "group_id": extract_group_ref(link)
        })
    with open(f"temp{i}.json", "w", encoding="utf-8") as file:
        json.dump(response, file, indent=4, ensure_ascii=False)
    
    i += 1
    response = await vk.request("wall.get", {
        "owner_id": link,
        "count": 100,
        "extended": 1
    })
    with open(f"temp{i}.json", "w", encoding="utf-8") as file:
        json.dump(response, file, indent=4, ensure_ascii=False)
    
    
    await message.answer("Done.", reply_markup=get_close_button())
    await loading_msg.delete()


@router.message(
    StateFilter(None),
    F.text.regexp(r"^(https?://)?(www\.)?(vk\.com|vk\.ru)/")
) # vk links
async def detect_vk_link(message: Message):
    text = message.text.strip()
    
    m = re.search(r"wall(-?\d+)_\d+", text)
    if m:
        owner_id = abs(int(m.group(1)))
        result = await vk.check_group(str(owner_id))
    else:
        result = await vk.check_group(text)
    
    if not result["ok"]:
        return
    
    group = result["group"]
    
    await message.reply(
        f"👁️ Обнаружена ссылка на группу "
        f'<i><a href="https://vk.com/{group.screen_name}">{group.name}</a></i>\n'
        "Желаете привязать ее к данному чату?",
        reply_markup=get_confirm_binding_menu(chat_id=message.chat.id, group_id=group.id),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message):
    await message.answer(
        "⚠️ <b>Неизвестная команда.</b>\n"
        "Используйте /help для открытия списка команд",
        parse_mode="HTML"
    )