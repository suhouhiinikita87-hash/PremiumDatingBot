import asyncio
import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, ADMIN_ID
from database import *
from keyboards import *

# Инициализация
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
init_db()

# --- Состояния ---
class RegisterState(StatesGroup):
    name = State()
    age = State()
    city = State()
    gender = State()
    looking_for = State()
    bio = State()
    photo = State()

class EditProfileState(StatesGroup):
    waiting_for = State()

class FilterState(StatesGroup):
    min_age = State()
    max_age = State()
    city = State()

class MailingState(StatesGroup):
    message = State()

class ChatState(StatesGroup):
    waiting_for_message = State()

# --- СТАРТ ---
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    user = get_user(tg_id)
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = int(args[1].split("_")[1])
        if referrer_id != tg_id and not get_user(tg_id):
            add_referral(referrer_id, tg_id)
            await message.answer(f"🎉 Вы пришли по реферальной ссылке!")
    
    if user:
        premium_status = "✅ Активен" if is_premium(tg_id) else "❌ Не активен"
        await message.answer(
            f"👋 С возвращением, {user['name']}!\n\n"
            f"⭐ Premium: {premium_status}\n"
            f"🎁 Бонусов: {get_bonus_balance(tg_id)}\n"
            f"👥 Пользователей: {get_user_count()}",
            reply_markup=main_menu(is_premium(tg_id))
        )
    else:
        await message.answer(
            "🌟 Добро пожаловать в Premium Dating Bot!\n\n"
            "Давай создадим твою анкету. Как тебя зовут?"
        )
        await state.set_state(RegisterState.name)

# --- РЕГИСТРАЦИЯ ---
@dp.message(RegisterState.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("🎂 Сколько тебе лет? (только число)")
    await state.set_state(RegisterState.age)

@dp.message(RegisterState.age)
async def reg_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Напиши число!")
        return
    await state.update_data(age=int(message.text))
    await message.answer("🏙️ Из какого ты города?")
    await state.set_state(RegisterState.city)

@dp.message(RegisterState.city)
async def reg_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("👤 Твой пол:", reply_markup=gender_keyboard())
    await state.set_state(RegisterState.gender)

@dp.callback_query(RegisterState.gender, F.data.startswith("gender_"))
async def reg_gender(call: CallbackQuery, state: FSMContext):
    gender_map = {"gender_male": "Мужской", "gender_female": "Женский", "gender_other": "Другой"}
    await state.update_data(gender=gender_map[call.data])
    await call.message.edit_text("👥 Кого ты ищешь?", reply_markup=looking_for_keyboard())
    await state.set_state(RegisterState.looking_for)
    await call.answer()

@dp.callback_query(RegisterState.looking_for, F.data.startswith("looking_"))
async def reg_looking_for(call: CallbackQuery, state: FSMContext):
    looking_map = {"looking_female": "Девушку", "looking_male": "Парня", "looking_friends": "Друзей", "looking_any": "Не важно"}
    await state.update_data(looking_for=looking_map[call.data])
    await call.message.edit_text("📝 Напиши немного о себе (увлечения, цели, интересы):")
    await state.set_state(RegisterState.bio)
    await call.answer()

@dp.message(RegisterState.bio)
async def reg_bio(message: Message, state: FSMContext):
    await state.update_data(bio=message.text)
    await message.answer("📷 Отправь своё фото:")
    await state.set_state(RegisterState.photo)

@dp.message(RegisterState.photo, F.photo)
async def reg_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    
    os.makedirs("photos", exist_ok=True)
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    photo_path = f"photos/{message.from_user.id}.jpg"
    await bot.download_file(file.file_path, photo_path)
    
    user_data = {
        "name": data["name"],
        "age": data["age"],
        "city": data["city"],
        "gender": data["gender"],
        "looking_for": data["looking_for"],
        "bio": data["bio"],
        "photo": photo_path,
        "premium_until": None,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "referrer_id": None,
        "bonus_balance": 0
    }
    save_user(message.from_user.id, user_data)
    
    await message.answer(
        "✅ Анкета создана!\n\n"
        f"👤 Имя: {data['name']}\n"
        f"🎂 Возраст: {data['age']}\n"
        f"🏙️ Город: {data['city']}\n"
        f"👥 Ищу: {data['looking_for']}\n\n"
        "🔍 Используй кнопку 'Искать анкеты' для поиска!",
        reply_markup=main_menu()
    )
    await state.clear()

# --- ПОИСК АНКЕТ ---
@dp.message(F.text == "🔍 Искать анкеты")
async def search_profiles(message: Message):
    tg_id = message.from_user.id
    user = get_user(tg_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйся через /start")
        return
    
    candidates = get_search_candidates(tg_id)
    if not candidates:
        await message.answer("😔 Пока нет других пользователей. Зайди позже!")
        return
    
    await message.answer(f"🔍 Найдено {len(candidates)} анкет. Начинаем показ...")
    
    for cand in candidates:
        cand_tg_id, name, age, city, photo_path, bio = cand
        
        if is_blocked(tg_id, cand_tg_id):
            continue
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM likes WHERE from_tg_id = ? AND to_tg_id = ?", (tg_id, cand_tg_id))
        already_liked = cursor.fetchone() is not None
        conn.close()
        
        caption = f"👤 {name}, {age} лет\n🏙️ {city}\n\n📝 {bio[:200] if bio else 'Не указано'}"
        
        if photo_path and os.path.exists(photo_path):
            photo = FSInputFile(photo_path)
            await message.answer_photo(photo, caption=caption, reply_markup=profile_actions(cand_tg_id, already_liked))
        else:
            await message.answer(caption, reply_markup=profile_actions(cand_tg_id, already_liked))
        
        await asyncio.sleep(0.5)

# --- ЛАЙКИ ---
@dp.callback_query(F.data.startswith("like_"))
async def like_profile(call: CallbackQuery):
    from_tg = call.from_user.id
    to_tg = int(call.data.split("_")[1])
    
    if add_like(from_tg, to_tg):
        if check_match(from_tg, to_tg):
            to_user = get_user(to_tg)
            from_user = get_user(from_tg)
            chat_id = get_or_create_chat(from_tg, to_tg)
            if to_user:
                await bot.send_message(
                    to_tg,
                    f"💘 У Вас взаимная симпатия с {from_user['name']}!\n\n"
                    f"Используйте кнопку '💬 Мои чаты' в меню."
                )
            await call.message.edit_reply_markup(reply_markup=None)
            await call.answer("🎉 Взаимная симпатия! Чат создан!", show_alert=True)
        else:
            await call.answer("❤️ Лайк отправлен!")
    else:
        await call.answer("❌ Вы уже лайкали этого пользователя")

# --- ЖАЛОБЫ ---
@dp.callback_query(F.data.startswith("report_"))
async def report_profile(call: CallbackQuery):
    to_tg = int(call.data.split("_")[1])
    user = get_user(to_tg)
    if user and user.get("photo"):
        add_report(call.from_user.id, to_tg, user["photo"], "жалоба на фото")
        await call.answer("✅ Жалоба отправлена модератору", show_alert=True)
    else:
        await call.answer("❌ Ошибка", show_alert=True)

# --- МОЯ АНКЕТА ---
@dp.message(F.text == "👤 Моя анкета")
async def my_profile(message: Message):
    tg_id = message.from_user.id
    user = get_user(tg_id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы. Напишите /start")
        return
    
    caption = (
        f"👤 <b>{user['name']}</b>, {user['age']} лет\n"
        f"🏙️ {user['city']}\n"
        f"👥 Пол: {user['gender']}\n"
        f"🔍 Ищу: {user['looking_for']}\n\n"
        f"📝 {user['bio']}\n\n"
        f"⭐ Premium: {'✅ Да' if is_premium(tg_id) else '❌ Нет'}\n"
        f"🎁 Бонусов: {get_bonus_balance(tg_id)}"
    )
    
    try:
        if user['photo'] and os.path.exists(user['photo']):
            photo = FSInputFile(user['photo'])
            await message.answer_photo(photo, caption=caption, parse_mode="HTML", reply_markup=edit_profile_buttons())
        else:
            await message.answer(caption, parse_mode="HTML", reply_markup=edit_profile_buttons())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

# --- ЛАЙКНУЛИ МЕНЯ ---
@dp.message(F.text == "❤️ Лайкнули меня")
async def who_liked_me(message: Message):
    tg_id = message.from_user.id
    if not is_premium(tg_id):
        await message.answer("🔒 Функция доступна только Premium пользователям!", reply_markup=premium_keyboard())
        return
    
    likes = get_likes_to_me(tg_id)
    if not likes:
        await message.answer("😔 Пока никто не лайкнул тебя")
        return
    
    await message.answer(f"❤️ Тебя лайкнули {len(likes)} человек:")
    for like in likes:
        tg_id_like, name, age, city, photo_path = like
        text = f"👤 {name}, {age} лет, {city}"
        if photo_path and os.path.exists(photo_path):
            photo = FSInputFile(photo_path)
            await message.answer_photo(photo, caption=text)
        else:
            await message.answer(text)

# --- ЧАТЫ ---
@dp.message(F.text == "💬 Мои чаты")
async def list_chats(message: Message):
    tg_id = message.from_user.id
    chats = get_user_chats(tg_id)
    if not chats:
        await message.answer("💬 У вас пока нет чатов.")
        return
    await message.answer("💬 Ваши чаты:", reply_markup=user_chats_keyboard(chats, tg_id))

@dp.callback_query(F.data.startswith("open_chat_"))
async def open_chat(call: CallbackQuery, state: FSMContext):
    chat_id = int(call.data.split("_")[2])
    users = get_chat_users(chat_id)
    if not users:
        await call.answer("Чат не найден")
        return
    other_id = users[1] if call.from_user.id == users[0] else users[0]
    other_user = get_user(other_id)
    if not other_user:
        await call.answer("Пользователь не найден")
        return
    await call.message.edit_text(f"💬 Чат с {other_user['name']}\n\nНапишите сообщение:")
    await state.update_data(chat_id=chat_id)
    await state.set_state(ChatState.waiting_for_message)
    await call.answer()

@dp.message(ChatState.waiting_for_message)
async def send_message(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    if not chat_id:
        await message.answer("Ошибка чата")
        await state.clear()
        return
    users = get_chat_users(chat_id)
    if not users:
        await message.answer("Чат не найден")
        await state.clear()
        return
    other_id = users[1] if message.from_user.id == users[0] else users[0]
    save_message(chat_id, message.from_user.id, message.text)
    await bot.send_message(other_id, f"💬 {message.from_user.first_name}: {message.text}")
    await message.answer("✅ Сообщение отправлено!")

# --- РЕФЕРАЛЫ ---
@dp.message(F.text == "🎁 Рефералы")
async def referral_menu(message: Message):
    tg_id = message.from_user.id
    count = get_referral_count(tg_id)
    balance = get_bonus_balance(tg_id)
    await message.answer(
        f"🎁 Реферальная программа\n\n👥 Приглашено: {count}\n💰 Бонусов: {balance}",
        reply_markup=referral_keyboard()
    )

@dp.callback_query(F.data == "get_referral_link")
async def get_referral_link(call: CallbackQuery):
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{call.from_user.id}"
    await call.message.edit_text(f"🔗 Ваша ссылка:\n{link}")
    await call.answer()

@dp.callback_query(F.data == "buy_premium_bonus")
async def buy_premium_bonus(call: CallbackQuery):
    tg_id = call.from_user.id
    balance = get_bonus_balance(tg_id)
    if balance >= 200:
        use_bonus(tg_id, 200)
        update_premium(tg_id, 30)
        await call.message.edit_text("✅ Premium активирован на 30 дней за бонусы!")
    else:
        await call.message.edit_text(f"❌ Недостаточно бонусов. Нужно 200, у вас {balance}")
    await call.answer()

# --- PREMIUM ---
@dp.message(F.text == "⭐ Купить Premium")
async def buy_premium(message: Message):
    await message.answer(
        "🌟 Premium возможности:\n"
        "• Видеть, кто тебя лайкнул\n"
        "• Расширенный поиск\n"
        "• Приоритет в выдаче\n\n"
        "Выбери способ оплаты:",
        reply_markup=premium_keyboard()
    )

@dp.callback_query(F.data == "buy_with_bonus")
async def buy_premium_with_bonus(call: CallbackQuery):
    tg_id = call.from_user.id
    balance = get_bonus_balance(tg_id)
    if balance >= 200:
        use_bonus(tg_id, 200)
        update_premium(tg_id, 30)
        await call.message.edit_text("✅ Premium активирован на 30 дней!")
    else:
        await call.message.edit_text(f"❌ Недостаточно бонусов. Нужно 200, у вас {balance}")
    await call.answer()

# --- СТАТИСТИКА ---
@dp.message(F.text == "📊 Статистика")
async def stats(message: Message):
    await message.answer(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: {get_user_count()}\n"
        f"❤️ Лайков всего: {get_likes_count()}\n\n"
        f"💡 Совет: Купи Premium, чтобы выделяться!",
        parse_mode="HTML"
    )

# --- АДМИН ПАНЕЛЬ ---
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа")
        return
    await message.answer("🔧 Админ панель:", reply_markup=admin_keyboard())

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔ Нет доступа")
        return
    await call.message.edit_text(
        f"📊 Полная статистика:\n"
        f"👥 Пользователей: {get_user_count()}\n"
        f"❤️ Лайков: {get_likes_count()}"
    )
    await call.answer()

@dp.callback_query(F.data == "admin_users")
async def admin_users(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔ Нет доступа")
        return
    users = get_all_users()
    await call.message.edit_text(f"👥 Всего пользователей: {len(users)}")
    await call.answer()

@dp.callback_query(F.data == "admin_mailing")
async def admin_mailing(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔ Нет доступа")
        return
    await call.message.edit_text("📢 Введите текст рассылки:")
    await state.set_state(MailingState.message)
    await call.answer()

@dp.message(MailingState.message)
async def send_mailing(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text
    users = get_all_users()
    success = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, f"📢 <b>Рассылка</b>\n\n{text}", parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
    save_mailing(text, success)
    await message.answer(f"✅ Рассылка отправлена {success} пользователям")
    await state.clear()

@dp.callback_query(F.data == "admin_reports")
async def admin_reports(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔ Нет доступа")
        return
    reports = get_pending_reports()
    if not reports:
        await call.message.edit_text("📭 Нет активных жалоб")
        return
    await call.message.edit_text(
        f"📋 Активные жалобы: {len(reports)}",
        reply_markup=admin_reports_keyboard(reports)
    )
    await call.answer()

@dp.callback_query(F.data.startswith("review_report_"))
async def review_report(call: CallbackQuery):
    report_id = int(call.data.split("_")[2])
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
    report = cursor.fetchone()
    conn.close()
    if report:
        await call.message.edit_text(
            f"📋 Жалоба #{report_id}\n"
            f"От: {report[1]}\n"
            f"На: {report[2]}\n"
            f"Причина: {report[4]}\n"
            f"Дата: {report[5]}",
            reply_markup=review_report_keyboard(report_id)
        )
    await call.answer()

@dp.callback_query(F.data.startswith("approve_report_"))
async def approve_report(call: CallbackQuery):
    report_id = int(call.data.split("_")[2])
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT to_tg_id FROM reports WHERE id = ?', (report_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        block_user(ADMIN_ID, result[0])
        resolve_report(report_id, "approved")
        await call.message.edit_text(f"✅ Пользователь {result[0]} заблокирован")
    await call.answer()

@dp.callback_query(F.data.startswith("reject_report_"))
async def reject_report(call: CallbackQuery):
    report_id = int(call.data.split("_")[2])
    resolve_report(report_id, "rejected")
    await call.message.edit_text("❌ Жалоба отклонена")
    await call.answer()

@dp.callback_query(F.data == "admin_back")
async def admin_back(call: CallbackQuery):
    await call.message.edit_text("🔧 Админ панель:", reply_markup=admin_keyboard())
    await call.answer()

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    tg_id = call.from_user.id
    user = get_user(tg_id)
    if user:
        await call.message.edit_text(
            "👋 Главное меню",
            reply_markup=main_menu(is_premium(tg_id))
        )
    else:
        await call.message.edit_text("👋 Главное меню")
    await call.answer()

# --- ЗАПУСК ---
async def main():
    print("🚀 Бот Premium Dating запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
