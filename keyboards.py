from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Главное меню (Reply-кнопки внизу экрана)
def main_menu(premium=False):
    buttons = [
        [KeyboardButton(text="🔍 Искать анкеты")],
        [KeyboardButton(text="👤 Моя анкета")],
        [KeyboardButton(text="❤️ Лайкнули меня")],
        [KeyboardButton(text="⭐ Купить Premium")],
        [KeyboardButton(text="📊 Статистика")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Инлайн-кнопки под анкетой (лайк, жалоба)
def profile_actions(tg_id, liked=False):
    buttons = []
    if not liked:
        buttons.append([InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{tg_id}")])
    buttons.append([InlineKeyboardButton(text="📢 Пожаловаться", callback_data=f"report_{tg_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Кнопки для редактирования анкеты
def edit_profile_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить имя", callback_data="edit_name"),
         InlineKeyboardButton(text="🎂 Изменить возраст", callback_data="edit_age")],
        [InlineKeyboardButton(text="🏙️ Изменить город", callback_data="edit_city"),
         InlineKeyboardButton(text="📝 Изменить описание", callback_data="edit_bio")],
        [InlineKeyboardButton(text="🔄 Изменить пол", callback_data="edit_gender"),
         InlineKeyboardButton(text="👥 Кого ищу", callback_data="edit_looking_for")],
        [InlineKeyboardButton(text="📷 Изменить фото", callback_data="edit_photo")]
    ])

# Кнопки для выбора пола при регистрации
def gender_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male"),
         InlineKeyboardButton(text="👩 Женский", callback_data="gender_female")],
        [InlineKeyboardButton(text="⚧️ Другой", callback_data="gender_other")]
    ])

# Кнопки для выбора "кого ищу"
def looking_for_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👩 Девушку", callback_data="looking_female"),
         InlineKeyboardButton(text="👨 Парня", callback_data="looking_male")],
        [InlineKeyboardButton(text="👥 Друзей", callback_data="looking_friends"),
         InlineKeyboardButton(text="❤️ Не важно", callback_data="looking_any")]
    ])

# Кнопки покупки Premium
def premium_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 1 месяц - 150₽", callback_data="premium_30")],
        [InlineKeyboardButton(text="⭐ 3 месяца - 400₽", callback_data="premium_90")],
        [InlineKeyboardButton(text="⭐ 12 месяцев - 1200₽", callback_data="premium_365")],
        [InlineKeyboardButton(text="👁️ Посмотреть лайкнувших (50₽)", callback_data="buy_view_likes")]
    ])

# Админ-панель
def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="💌 Рассылка", callback_data="admin_mailing")],
        [InlineKeyboardButton(text="❌ Жалобы", callback_data="admin_reports")]
    ])