import asyncio
import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InputFile
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

# --- Состояния для регистрации ---
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

# --- ГЛАВНОЕ МЕНЮ ---
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    user = get_user(tg_id)
    
    if user:
        premium_status = "✅ Активен" if is_premium(tg_id) else "❌ Не активен"
        await message.answer(
            f"👋 С возвращением, {user['name']}!\n\n"
            f"⭐ Premium: {premium_status}\n"
            f"📊 Пользователей в боте: {get_user_count()}",
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
    
    # Сохраняем фото
    os.makedirs("photos", exist_ok=True)
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    photo_path = f"photos/{message.from_user.id}.jpg"
    await bot.download_file(file.file_path, photo_path)
    
    # Сохраняем пользователя
    user_data = {
        "name": data["name"],
        "age": data["age"],
        "city": data["city"],
        "gender": data["gender"],
        "looking_for": data["looking_for"],
        "bio": data["bio"],
        "photo": photo_path,
        "premium_until": None,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        
        # Проверяем, не ставил ли уже лайк
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM likes WHERE from_tg_id = ? AND to_tg_id = ?", (tg_id, cand_tg_id))
        already_liked = cursor.fetchone() is not None
        conn.close()
        
        caption = (
            f"👤 {name}, {age} лет\n"
            f"🏙️ {city}\n\n"
            f"📝 {bio[:200] if bio else 'Не указано'}"
        )
        
        if photo_path and os.path.exists(photo_path):
            photo = InputFile(photo_path)
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
            
            if to_user:
                await bot.send_message(
                    to_tg,
                    f"💘 У Вас взаимная симпатия с {from_user['name']}!\n\n"
                    f"Свяжитесь с ним/ней: https://t.me/{call.from_user.username or 'не указан'}"
                )
            await call.message.edit_reply_markup(reply_markup=None)
            await call.answer("🎉 Взаимная симпатия!", show_alert=True)
        else:
            await call.answer("❤️ Лайк отправлен!")
    else:
        await call.answer("❌ Вы уже лайкали этого пользователя")

# --- МОЯ АНКЕТА ---
@dp.message(F.text == "👤 Моя анкета")
async def my_profile(message: Message):
    tg_id = message.from_user.id
    user = get_user(tg_id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы. /start")
        return
    
    caption = (
        f"👤 <b>{user['name']}</b>, {user['age']} лет\n"
        f"🏙️ {user['city']}\n"
        f"👥 Пол: {user['gender']}\n"
        f"🔍 Ищу: {user['looking_for']}\n\n"
        f"📝 {user['bio']}\n\n"
        f"⭐ Premium: {'✅ Да' if is_premium(tg_id) else '❌ Нет'}"
    )
    
    if user['photo'] and os.path.exists(user['photo']):
        photo = InputFile(user['photo'])
        await message.answer_photo(photo, caption=caption, parse_mode="HTML", reply_markup=edit_profile_buttons())
    else:
        await message.answer(caption, parse_mode="HTML", reply_markup=edit_profile_buttons())

# --- КТО ЛАЙКНУЛ (только Premium) ---
@dp.message(F.text == "❤️ Лайкнули меня")
async def who_liked_me(message: Message):
    tg_id = message.from_user.id
    
    if not is_premium(tg_id):
        await message.answer(
            "🔒 Функция доступна только Premium пользователям!\n\n"
            "Купи Premium, чтобы видеть, кто тебя лайкнул:",
            reply_markup=premium_keyboard()
        )
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
            photo = InputFile(photo_path)
            await message.answer_photo(photo, caption=text)
        else:
            await message.answer(text)

# --- ПОКУПКА PREMIUM ---
@dp.message(F.text == "⭐ Купить Premium")
async def buy_premium(message: Message):
    await message.answer(
        "🌟 Premium возможности:\n"
        "• Видеть, кто тебя лайкнул\n"
        "• Расширенный поиск (по возрасту, городу)\n"
        "• Приоритет в выдаче\n"
        "• Без рекламы\n\n"
        "Выбери тариф:",
        reply_markup=premium_keyboard()
    )

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

# --- ЗАПУСК ---
async def main():
    print("🚀 Бот Premium Dating запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
