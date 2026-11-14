import sqlite3
import random
from datetime import datetime
from zoneinfo import ZoneInfo


def create_database():
    conn = sqlite3.connect("style_club.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            title TEXT,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price INTEGER
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM gifts")
    gifts_count = cursor.fetchone()[0]

    if gifts_count == 0:
        cursor.executemany(
            "INSERT INTO gifts (title, price) VALUES (?, ?)",
            [
                ("Скидка 5%", 100),
                ("Подарочный набор", 300),
                ("Сертификат на 500 ₽", 500)
            ]
        )
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wheel_spins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            spin_date TEXT NOT NULL,
            prize INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(telegram_id, spin_date)
        )
    """)
    conn.commit()
    conn.close()

def register_user(telegram_id, username, first_name):
    conn = sqlite3.connect("style_club.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO users (telegram_id, username, first_name)
        VALUES (?, ?, ?)
    """, (telegram_id, username, first_name))

    cursor.execute("""
        SELECT id FROM achievements
        WHERE telegram_id = ? AND title = ?
    """, (telegram_id, "Первый шаг"))

    achievement_exists = cursor.fetchone()

    if not achievement_exists:
        cursor.execute("""
            INSERT INTO achievements (telegram_id, title)
            VALUES (?, ?)
        """, (telegram_id, "Первый шаг"))

    conn.commit()
    conn.close()
      
def get_user(telegram_id):
    conn = sqlite3.connect("style_club.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT first_name, points FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )

    user = cursor.fetchone()
    conn.close()

    return user

def get_achievements(telegram_id):
    conn = sqlite3.connect("style_club.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT title, earned_at FROM achievements WHERE telegram_id = ?",
        (telegram_id,)
    )

    achievements = cursor.fetchall()
    conn.close()

    return achievements

def add_points(telegram_id, points):
    conn = sqlite3.connect("style_club.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET points = points + ? WHERE telegram_id = ?",
        (points, telegram_id)
    )

    conn.commit()
    conn.close()
def get_gifts():
    conn = sqlite3.connect("style_club.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, price FROM gifts")
    gifts = cursor.fetchall()

    conn.close()
    return gifts


def redeem_gift(telegram_id, gift_id):
    conn = sqlite3.connect("style_club.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT title, price FROM gifts WHERE id = ?",
        (gift_id,)
    )
    gift = cursor.fetchone()

    if not gift:
        conn.close()
        return "not_found", None

    title, price = gift

    cursor.execute(
        "SELECT points FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    user = cursor.fetchone()

    if not user:
        conn.close()
        return "no_user", None

    cursor.execute(
        "UPDATE users SET points = points - ? "
        "WHERE telegram_id = ? AND points >= ?",
        (price, telegram_id, price)
    )

    if cursor.rowcount == 0:
        conn.close()
        return "not_enough", title

    conn.commit()
    conn.close()

    return "success", title

def spin_wheel(telegram_id):
    conn = sqlite3.connect("style_club.db")
    cursor = conn.cursor()

    today = datetime.now(
        ZoneInfo("Asia/Yekaterinburg")
    ).date().isoformat()

    cursor.execute("BEGIN IMMEDIATE")

    cursor.execute(
        "SELECT points FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    user = cursor.fetchone()

    if not user:
        conn.rollback()
        conn.close()
        return "no_user", None

    cursor.execute(
        "SELECT id FROM wheel_spins WHERE telegram_id = ? AND spin_date = ?",
        (telegram_id, today)
    )

    if cursor.fetchone():
        conn.rollback()
        conn.close()
        return "already_spun", None

    prize = random.choice([0, 5, 10, 25, 50, 100])

    cursor.execute(
        "INSERT INTO wheel_spins (telegram_id, spin_date, prize) VALUES (?, ?, ?)",
        (telegram_id, today, prize)
    )

    cursor.execute(
        "UPDATE users SET points = points + ? WHERE telegram_id = ?",
        (prize, telegram_id)
    )

    conn.commit()
    conn.close()

    return "success", prize