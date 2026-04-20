import sqlite3
from datetime import datetime, timedelta

DB_NAME = "dating.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            city TEXT,
            gender TEXT,
            looking_for TEXT,
            bio TEXT,
            photo TEXT,
            premium_until TEXT,
            created_at TEXT
        )
    ''')
    
    # Добавляем недостающие колонки (миграция для старых баз)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN referrer_id INTEGER')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN bonus_balance INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    
    # Таблица лайков
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_tg_id INTEGER,
            to_tg_id INTEGER,
            created_at TEXT,
            UNIQUE(from_tg_id, to_tg_id)
        )
    ''')
    
    # Таблица чатов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER,
            user2_id INTEGER,
            created_at TEXT,
            UNIQUE(user1_id, user2_id)
        )
    ''')
    
    # Таблица сообщений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            from_id INTEGER,
            text TEXT,
            created_at TEXT
        )
    ''')
    
    # Таблица рефералов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            created_at TEXT
        )
    ''')
    
    # Таблица рассылок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mailing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            sent_at TEXT,
            recipients_count INTEGER
        )
    ''')
    
    # Таблица жалоб
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_tg_id INTEGER,
            to_tg_id INTEGER,
            photo_path TEXT,
            reason TEXT,
            created_at TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    # Таблица блокировок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blocker_id INTEGER,
            blocked_id INTEGER,
            created_at TEXT,
            UNIQUE(blocker_id, blocked_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# --- ОСТАЛЬНЫЕ ФУНКЦИИ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ ---
# (все функции get_user, save_user, add_like и т.д. остаются как были)

def get_user(tg_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        # Определяем количество колонок в таблице
        if len(user) == 11:
            return {
                "tg_id": user[0],
                "name": user[1],
                "age": user[2],
                "city": user[3],
                "gender": user[4],
                "looking_for": user[5],
                "bio": user[6],
                "photo": user[7],
                "premium_until": user[8],
                "created_at": user[9],
                "referrer_id": user[10] if len(user) > 10 else None,
                "bonus_balance": user[11] if len(user) > 11 else 0
            }
        else:
            return {
                "tg_id": user[0],
                "name": user[1],
                "age": user[2],
                "city": user[3],
                "gender": user[4],
                "looking_for": user[5],
                "bio": user[6],
                "photo": user[7],
                "premium_until": user[8],
                "created_at": user[9],
                "referrer_id": None,
                "bonus_balance": 0
            }
    return None

def save_user(tg_id, data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (tg_id, name, age, city, gender, looking_for, bio, photo, premium_until, created_at, referrer_id, bonus_balance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tg_id, data["name"], data["age"], data["city"], data["gender"], 
          data["looking_for"], data["bio"], data["photo"], data.get("premium_until"), data.get("created_at"),
          data.get("referrer_id"), data.get("bonus_balance", 0)))
    conn.commit()
    conn.close()

def update_premium(tg_id, days):
    user = get_user(tg_id)
    if user and user.get("premium_until"):
        old_date = datetime.strptime(user["premium_until"], "%Y-%m-%d %H:%M:%S")
        new_date = old_date + timedelta(days=days)
    else:
        new_date = datetime.now() + timedelta(days=days)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET premium_until = ? WHERE tg_id = ?", (new_date.strftime("%Y-%m-%d %H:%M:%S"), tg_id))
    conn.commit()
    conn.close()

def is_premium(tg_id):
    user = get_user(tg_id)
    if not user or not user.get("premium_until"):
        return False
    premium_until = datetime.strptime(user["premium_until"], "%Y-%m-%d %H:%M:%S")
    return premium_until > datetime.now()

def add_like(from_tg, to_tg):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO likes (from_tg_id, to_tg_id, created_at) VALUES (?, ?, ?)",
                       (from_tg, to_tg, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def check_match(from_tg, to_tg):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM likes WHERE from_tg_id = ? AND to_tg_id = ?", (to_tg, from_tg))
    match = cursor.fetchone()
    conn.close()
    return match is not None

def get_likes_to_me(tg_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.tg_id, u.name, u.age, u.city, u.photo 
        FROM likes l
        JOIN users u ON l.from_tg_id = u.tg_id
        WHERE l.to_tg_id = ?
    ''', (tg_id,))
    likes = cursor.fetchall()
    conn.close()
    return likes

def get_search_candidates(tg_id, filters=None):
    user = get_user(tg_id)
    if not user:
        return []
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT tg_id, name, age, city, photo, bio FROM users WHERE tg_id != ?"
    params = [tg_id]
    
    query += " AND tg_id NOT IN (SELECT blocked_id FROM blocks WHERE blocker_id = ?)"
    params.append(tg_id)
    
    if filters:
        if filters.get("gender"):
            query += " AND gender = ?"
            params.append(filters["gender"])
        if filters.get("looking_for"):
            query += " AND looking_for = ?"
            params.append(filters["looking_for"])
        if filters.get("min_age"):
            query += " AND age >= ?"
            params.append(filters["min_age"])
        if filters.get("max_age"):
            query += " AND age <= ?"
            params.append(filters["max_age"])
        if filters.get("city"):
            query += " AND city = ?"
            params.append(filters["city"])
    
    cursor.execute(query, params)
    users = cursor.fetchall()
    conn.close()
    return users

def get_user_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_likes_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM likes")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_or_create_chat(user1_id, user2_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM chats 
        WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    ''', (user1_id, user2_id, user2_id, user1_id))
    chat = cursor.fetchone()
    if chat:
        conn.close()
        return chat[0]
    cursor.execute('''
        INSERT INTO chats (user1_id, user2_id, created_at)
        VALUES (?, ?, ?)
    ''', (user1_id, user2_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return chat_id

def save_message(chat_id, from_id, text):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (chat_id, from_id, text, created_at)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, from_id, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_chat_messages(chat_id, limit=50):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT from_id, text, created_at FROM messages
        WHERE chat_id = ?
        ORDER BY created_at DESC LIMIT ?
    ''', (chat_id, limit))
    messages = cursor.fetchall()
    conn.close()
    return messages[::-1]

def get_chat_users(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user1_id, user2_id FROM chats WHERE id = ?', (chat_id,))
    users = cursor.fetchone()
    conn.close()
    return users

def get_user_chats(tg_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user1_id, user2_id, created_at FROM chats 
        WHERE user1_id = ? OR user2_id = ?
        ORDER BY created_at DESC
    ''', (tg_id, tg_id))
    chats = cursor.fetchall()
    conn.close()
    return chats

def add_referral(referrer_id, referred_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM referrals WHERE referred_id = ?', (referred_id,))
    if cursor.fetchone():
        conn.close()
        return False
    cursor.execute('''
        INSERT INTO referrals (referrer_id, referred_id, created_at)
        VALUES (?, ?, ?)
    ''', (referrer_id, referred_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    cursor.execute('UPDATE users SET bonus_balance = bonus_balance + 50 WHERE tg_id = ?', (referrer_id,))
    conn.commit()
    conn.close()
    return True

def get_referral_count(tg_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (tg_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_bonus_balance(tg_id):
    user = get_user(tg_id)
    return user.get("bonus_balance", 0) if user else 0

def use_bonus(tg_id, amount):
    balance = get_bonus_balance(tg_id)
    if balance >= amount:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET bonus_balance = bonus_balance - ? WHERE tg_id = ?', (amount, tg_id))
        conn.commit()
        conn.close()
        return True
    return False

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT tg_id FROM users')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def save_mailing(message, recipients_count):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO mailing (message, sent_at, recipients_count)
        VALUES (?, ?, ?)
    ''', (message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), recipients_count))
    conn.commit()
    conn.close()

def add_report(from_tg, to_tg, photo_path, reason="интимное фото"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (from_tg_id, to_tg_id, photo_path, reason, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (from_tg, to_tg, photo_path, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pending"))
    conn.commit()
    conn.close()

def block_user(blocker_id, blocked_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO blocks (blocker_id, blocked_id, created_at) VALUES (?, ?, ?)',
                       (blocker_id, blocked_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def is_blocked(blocker_id, blocked_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (blocker_id, blocked_id))
    blocked = cursor.fetchone() is not None
    conn.close()
    return blocked

def get_pending_reports():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reports WHERE status = "pending" ORDER BY created_at DESC')
    reports = cursor.fetchall()
    conn.close()
    return reports

def resolve_report(report_id, action="approved"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE reports SET status = ? WHERE id = ?', (action, report_id))
    conn.commit()
    conn.close()
