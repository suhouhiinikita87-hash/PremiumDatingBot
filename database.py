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
    
    # Таблица просмотров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_tg_id INTEGER,
            to_tg_id INTEGER,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user(tg_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
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
            "created_at": user[9]
        }
    return None

def save_user(tg_id, data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (tg_id, name, age, city, gender, looking_for, bio, photo, premium_until, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tg_id, data["name"], data["age"], data["city"], data["gender"], 
          data["looking_for"], data["bio"], data["photo"], data.get("premium_until"), data.get("created_at")))
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