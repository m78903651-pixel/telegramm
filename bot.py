import asyncio
import logging
from typing import List, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, BotCommand
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = "8027071950:AAFhDL4KuTyFYPEraHpnRAj-P3TUDcTNfZQ"  # Замените на реальный токен
OWNER_ID = 6794991528  # Замените на ваш Telegram ID
OWNER_USERNAME = "sqico"  # Замените на ваш username (без @)

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- ХРАНИЛИЩЕ ДАННЫХ ---
account_link: Optional[str] = None
ads_list: List[str] = []

# --- КЛАВИАТУРЫ ---
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура с кнопками"""
    buttons = [
        [KeyboardButton(text="👤 Аккаунт")],
        [KeyboardButton(text="📞 Связь")],
        [KeyboardButton(text="🛒 В продаже")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_ads_navigation_keyboard(current_index: int, total: int) -> Optional[InlineKeyboardMarkup]:
    """Клавиатура для навигации по объявлениям"""
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"prev_{current_index}"))
    if current_index < total - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"next_{current_index}"))
    
    if nav_buttons:
        return InlineKeyboardMarkup(inline_keyboard=[nav_buttons])
    return None

# --- КОМАНДЫ ---
@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Приветственное сообщение"""
    await message.answer(
        "🤖 <b>Добро пожаловать в магазин!</b>\n\n"
        "Используйте кнопки внизу экрана:\n\n"
        "👤 <b>Аккаунт</b> - ссылка на профиль продавца\n"
        "📞 <b>Связь</b> - связаться с продавцом\n"
        "🛒 <b>В продаже</b> - список товаров",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("add"))
async def cmd_add_link(message: Message, command: CommandObject) -> None:
    """Установить ссылку для кнопки Аккаунт"""
    global account_link
    
    # Проверка прав
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return
    
    # Получаем аргументы
    if command.args is None or command.args.strip() == "":
        await message.answer(
            "❌ <b>Использование:</b>\n"
            "/add https://ссылка\n\n"
            "<b>Пример:</b>\n"
            "/add https://t.me/username"
        )
        return
    
    account_link = command.args.strip()
    await message.answer(
        f"✅ <b>Ссылка для кнопки «Аккаунт» установлена!</b>\n\n"
        f"{account_link}"
    )

@dp.message(Command("sett"))
async def cmd_add_ad(message: Message, command: CommandObject) -> None:
    """Добавить новое объявление"""
    global ads_list
    
    # Проверка прав
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return
    
    # Получаем аргументы
    if command.args is None or command.args.strip() == "":
        await message.answer(
            "❌ <b>Использование:</b>\n"
            "/sett Текст объявления\n\n"
            "<b>Пример:</b>\n"
            "/sett Продаю iPhone 13, состояние отличное"
        )
        return
    
    ads_list.append(command.args.strip())
    await message.answer(
        f"✅ <b>Объявление добавлено!</b>\n\n"
        f"📦 Всего в продаже: {len(ads_list)}"
    )

@dp.message(Command("list"))
async def cmd_list_ads(message: Message) -> None:
    """Показать все объявления (для владельца)"""
    # Проверка прав
    if message.from_user.id != OWNER_ID:
        return
    
    if not ads_list:
        await message.answer("📭 Список объявлений пуст.")
        return
    
    # Формируем список
    text_parts = []
    current_text = "<b>📋 Все объявления:</b>\n\n"
    
    for i, ad in enumerate(ads_list, 1):
        ad_preview = ad[:100] + "..." if len(ad) > 100 else ad
        new_entry = f"<b>{i}.</b> {ad_preview}\n\n"
        
        # Если текст превышает лимит, отправляем текущую часть и начинаем новую
        if len(current_text + new_entry) > 4096:
            text_parts.append(current_text)
            current_text = "<b>📋 Все объявления (продолжение):</b>\n\n" + new_entry
        else:
            current_text += new_entry
    
    # Добавляем последнюю часть
    text_parts.append(current_text)
    
    # Отправляем все части
    for part in text_parts:
        await message.answer(part)

@dp.message(Command("del"))
async def cmd_delete_ad(message: Message, command: CommandObject) -> None:
    """Удалить объявление по номеру"""
    # Проверка прав
    if message.from_user.id != OWNER_ID:
        return
    
    # Проверяем аргументы
    if command.args is None or not command.args.strip().isdigit():
        await message.answer("❌ Использование: /del <номер объявления>\n\nПример: /del 1")
        return
    
    index = int(command.args.strip()) - 1
    
    if 0 <= index < len(ads_list):
        deleted = ads_list.pop(index)
        await message.answer(f"✅ Объявление удалено:\n\n{deleted[:200]}")
    else:
        await message.answer(f"❌ Объявление с номером {index + 1} не найдено. Всего объявлений: {len(ads_list)}")

# --- ОБРАБОТКА КНОПОК ПОЛЬЗОВАТЕЛЯ ---
@dp.message(F.text == "👤 Аккаунт")
async def handle_account_button(message: Message) -> None:
    """Кнопка 'Аккаунт' - показывает ссылку"""
    if account_link:
        await message.answer(
            f"<b>👤 Это мой аккаунт, плеерок!</b>\n\n"
            f"Если вы хотите что-то купить, нажмите сюда:\n"
            f"<a href='{account_link}'>🔗 Перейти в аккаунт</a>",
            disable_web_page_preview=True
        )
    else:
        await message.answer(
            "⚠️ <b>Ссылка на аккаунт еще не установлена.</b>\n\n"
            "Пожалуйста, обратитесь к владельцу бота."
        )

@dp.message(F.text == "📞 Связь")
async def handle_contact_button(message: Message) -> None:
    """Кнопка 'Связь' - дает username владельца"""
    # Проверяем, установлен ли username и не является ли он заглушкой
    if OWNER_USERNAME and OWNER_USERNAME != "username_vladelca" and OWNER_USERNAME.strip():
        await message.answer(
            f"<b>📞 Связаться с продавцом</b>\n\n"
            f"Напишите мне напрямую:\n"
            f"<a href='https://t.me/{OWNER_USERNAME}'>👉 @{OWNER_USERNAME}</a>\n\n"
            f"Нажмите на ссылку выше, чтобы открыть чат.",
            disable_web_page_preview=True
        )
    else:
        # Если username не указан, используем ID
        await message.answer(
            f"<b>📞 Связаться с продавцом</b>\n\n"
            f"Напишите мне напрямую:\n"
            f"<a href='tg://user?id={OWNER_ID}'>👉 Написать продавцу</a>\n\n"
            f"Нажмите на ссылку, чтобы открыть чат.",
            disable_web_page_preview=True
        )

@dp.message(F.text == "🛒 В продаже")
async def handle_ads_button(message: Message) -> None:
    """Кнопка 'В продаже' - показывает первое объявление"""
    if not ads_list:
        await message.answer(
            "📭 <b>На данный момент нет товаров в продаже.</b>\n\n"
            "Загляните позже!"
        )
        return
    
    # Сохраняем информацию о текущем сообщении для навигации
    keyboard = get_ads_navigation_keyboard(0, len(ads_list))
    await message.answer(
        f"<b>📦 Товар 1 из {len(ads_list)}</b>\n\n"
        f"{ads_list[0]}",
        reply_markup=keyboard
    )

# --- НАВИГАЦИЯ ПО ОБЪЯВЛЕНИЯМ ---
@dp.callback_query(F.data.startswith("prev_"))
@dp.callback_query(F.data.startswith("next_"))
async def handle_ads_navigation(callback: CallbackQuery) -> None:
    """Обработка нажатий на кнопки вперед/назад"""
    try:
        # Парсим callback_data
        data = callback.data
        if not data or "_" not in data:
            await callback.answer("Ошибка навигации", show_alert=False)
            return
        
        parts = data.split("_")
        if len(parts) != 2:
            await callback.answer("Ошибка формата", show_alert=False)
            return
        
        action = parts[0]
        try:
            current_index = int(parts[1])
        except ValueError:
            await callback.answer("Ошибка индекса", show_alert=False)
            return
        
        # Проверяем, что список объявлений не пуст
        if not ads_list:
            await callback.message.delete()
            await callback.answer("Список объявлений пуст", show_alert=True)
            return
        
        # Вычисляем новый индекс
        if action == "prev":
            new_index = current_index - 1
        elif action == "next":
            new_index = current_index + 1
        else:
            await callback.answer("Неизвестное действие", show_alert=False)
            return
        
        # Проверяем границы
        if new_index < 0 or new_index >= len(ads_list):
            await callback.answer("📌 Это крайнее объявление", show_alert=False)
            return
        
        # Обновляем сообщение
        keyboard = get_ads_navigation_keyboard(new_index, len(ads_list))
        await callback.message.edit_text(
            f"<b>📦 Товар {new_index + 1} из {len(ads_list)}</b>\n\n"
            f"{ads_list[new_index]}",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logging.error(f"Ошибка в навигации: {e}")
        await callback.answer("Произошла ошибка", show_alert=False)

# --- ОБРАБОТЧИК ВСЕХ ОСТАЛЬНЫХ СООБЩЕНИЙ ---
@dp.message(F.text)
async def handle_other_messages(message: Message) -> None:
    """Обработка всех остальных текстовых сообщений"""
    await message.answer(
        "❓ Используйте кнопки внизу экрана для навигации:\n\n"
        "👤 Аккаунт\n"
        "📞 Связь\n"
        "🛒 В продаже",
        reply_markup=get_main_keyboard()
    )

# --- ЗАПУСК БОТА ---
async def main() -> None:
    """Главная функция запуска бота"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Установка команд бота (ИСПРАВЛЕННЫЙ СИНТАКСИС)
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="add", description="[Владелец] Установить ссылку аккаунта"),
        BotCommand(command="sett", description="[Владелец] Добавить товар"),
        BotCommand(command="list", description="[Владелец] Список всех товаров"),
        BotCommand(command="del", description="[Владелец] Удалить товар по номеру"),
    ])
    
    # Выводим информацию в консоль
    print("=" * 50)
    print("🚀 Бот успешно запущен!")
    print(f"📊 Статистика: {len(ads_list)} товаров в продаже")
    
    if OWNER_USERNAME and OWNER_USERNAME != "username_vladelca" and OWNER_USERNAME.strip():
        print(f"👤 Владелец: @{OWNER_USERNAME}")
    else:
        print(f"👤 Владелец ID: {OWNER_ID}")
    
    print("=" * 50)
    
    # Запускаем поллинг
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())