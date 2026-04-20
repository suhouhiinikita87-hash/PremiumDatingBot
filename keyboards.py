from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Главное меню
def main_menu(premium=False):
    buttons = [
        [KeyboardButton(text="🔍 Искать анкеты")],
        [KeyboardButton(text="👤 Моя анкета")],
        [KeyboardButton(text="❤️ Лайкнули меня")],
        [KeyboardButton(text="💬 Мои чаты")],
        [KeyboardButton(text="🎁 Рефералы")],
        [KeyboardButton(text="⭐ Купить Premium")],
        [KeyboardButton(text="📊 Статистика")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Кнопки под анкетой
def profile_actions(tg_id, liked=False):
    buttons = []
    if not liked:
        buttons.append([InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{tg_id}")])
    buttons.append([InlineKeyboardButton(text="📢 Пожаловаться", callback_data=f"report_{tg_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Редактирование анкеты
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

# Выбор пола
def gender_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male"),
         InlineKeyboardButton(text="👩 Женский", callback_data="gender_female")],
        [InlineKeyboardButton(text="⚧️ Другой", callback_data="gender_other")]
    ])

# Кого ищу
def looking_for_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👩 Девушку", callback_data="looking_female"),
         InlineKeyboardButton(text="👨 Парня", callback_data="looking_male")],
        [InlineKeyboardButton(text="👥 Друзей", callback_data="looking_friends"),
         InlineKeyboardButton(text="❤️ Не важно", callback_data="looking_any")]
    ])

# Premium покупка
def premium_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 1 месяц - 150₽", callback_data="premium_30")],
        [InlineKeyboardButton(text="⭐ 3 месяца - 400₽", callback_data="premium_90")],
        [InlineKeyboardButton(text="⭐ 12 месяцев - 1200₽", callback_data="premium_365")],
        [InlineKeyboardButton(text="👁️ Посмотреть лайкнувших (50₽)", callback_data="buy_view_likes")],
        [InlineKeyboardButton(text="🎁 Купить за бонусы", callback_data="buy_with_bonus")]
    ])

# Админ панель
def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_mailing")],
        [InlineKeyboardButton(text="❌ Жалобы", callback_data="admin_reports")]
    ])

# Фильтры поиска
def filters_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎂 По возрасту", callback_data="filter_age"),
         InlineKeyboardButton(text="🏙️ По городу", callback_data="filter_city")],
        [InlineKeyboardButton(text="🔄 Сбросить фильтры", callback_data="filter_reset")],
        [InlineKeyboardButton(text="🔍 Искать", callback_data="filter_search")]
    ])

# Возрастные фильтры
def age_filter_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="18-25", callback_data="age_18_25"),
         InlineKeyboardButton(text="26-35", callback_data="age_26_35")],
        [InlineKeyboardButton(text="36-45", callback_data="age_36_45"),
         InlineKeyboardButton(text="46+", callback_data="age_46_100")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="filter_back")]
    ])

# Клавиатура чата
def chat_keyboard(chat_id, other_user_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Написать сообщение", callback_data=f"chat_msg_{chat_id}")],
        [InlineKeyboardButton(text="🚫 Заблокировать чат", callback_data=f"chat_block_{chat_id}")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])

def back_to_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])

# Реферальная программа
def referral_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Моя реферальная ссылка", callback_data="get_referral_link")],
        [InlineKeyboardButton(text="🎁 Купить Premium за бонусы", callback_data="buy_premium_bonus")]
    ])

# Модерация жалоб
def admin_reports_keyboard(reports):
    buttons = []
    for report in reports[:10]:
        report_id, from_tg, to_tg, photo_path, reason, created_at, status = report
        buttons.append([InlineKeyboardButton(
            text=f"Жалоба #{report_id} от {from_tg} на {to_tg}",
            callback_data=f"review_report_{report_id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def review_report_keyboard(report_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить (заблокировать пользователя)", callback_data=f"approve_report_{report_id}")],
        [InlineKeyboardButton(text="❌ Отклонить (оставить как есть)", callback_data=f"reject_report_{report_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ])

# Список чатов пользователя
def user_chats_keyboard(chats, user_id):
    buttons = []
    for chat_id, user1_id, user2_id, created_at in chats:
        other_id = user2_id if user1_id == user_id else user1_id
        buttons.append([InlineKeyboardButton(
            text=f"💬 Чат с {other_id}",
            callback_data=f"open_chat_{chat_id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
