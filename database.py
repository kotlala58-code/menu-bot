import sqlite3
from datetime import datetime, timedelta

DB_NAME = "menu.db"

DAYS_RU = [
    "Понедельник", "Вторник", "Среда",
    "Четверг", "Пятница", "Суббота", "Воскресенье"
]

def get_today_name():
    return DAYS_RU[datetime.now().weekday()]

def get_tomorrow_name():
    return DAYS_RU[(datetime.now() + timedelta(days=1)).weekday()]

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute("DROP TABLE IF EXISTS dishes")
    
    cur.execute("""
        CREATE TABLE dishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            price INTEGER NOT NULL
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            username TEXT,
            text TEXT,
            date TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id INTEGER PRIMARY KEY,
            reminder_time TEXT
        )
    """)
    
    # Меню (убрал Хлеб из напитков)
    menu = {
        "Понедельник": [
            ("завтрак", "Запеканка", 100), ("завтрак", "Оладушки", 70),
            ("салат", "Пикантный", 90), ("салат", "Фасолевый", 90),
            ("первое", "Щи", 70),
            ("гарнир", "Рис", 70), ("гарнир", "Греча", 70), ("гарнир", "Макароны", 70), 
            ("гарнир", "Пюре", 70), ("гарнир", "Капуста тушеная", 70),
            ("мясо", "Плов", 70), ("мясо", "Котлеты куриные", 120), ("мясо", "Котлеты свиные", 90), 
            ("мясо", "Гуляш", 90), ("мясо", "Рыба (в кляре)", 90), 
            ("мясо", "Шницель", 90), ("мясо", "Мясо по-французски", 120),
            ("напиток", "Чай черный", 15), ("напиток", "Кофе 3 в 1", 30), 
            ("напиток", "Компот", 25), ("напиток", "Сок", 30),
        ],
        "Вторник": [
            ("завтрак", "Сырники", 100), ("завтрак", "Омлет", 120),
            ("салат", "Оливье", 90), ("салат", "Свежая капуста", 70),
            ("первое", "Рассольник", 70),
            ("гарнир", "Рис", 70), ("гарнир", "Греча", 70), ("гарнир", "Макароны", 70), 
            ("гарнир", "Пюре", 70), ("гарнир", "Капуста тушеная", 70), 
            ("мясо", "Котлета царская", 140), ("мясо", "Рыба жареная", 100), 
            ("мясо", "Котлеты рыбные", 90), ("мясо", "Печень", 120), 
            ("мясо", "Шницель", 90), ("мясо", "Мясо по-французски", 120), ("мясо", "Драники", 90),
            ("напиток", "Чай черный", 15), ("напиток", "Кофе 3 в 1", 30), 
            ("напиток", "Сок", 30),
        ],
        "Среда": [
            ("завтрак", "Оладьи", 70),
            ("салат", "Винегрет", 80), ("салат", "Салат", 100),
            ("первое", "Борщ", 70),
            ("гарнир", "Рис", 70), ("гарнир", "Греча", 70), ("гарнир", "Макароны", 70), 
            ("гарнир", "Пюре", 70), ("гарнир", "Капуста тушеная", 70),
            ("мясо", "Плов", 70), ("мясо", "Котлеты куриные", 120), ("мясо", "Котлеты свиные", 90), 
            ("мясо", "Гуляш", 90), ("мясо", "Рыба (в кляре)", 100), 
            ("мясо", "Шницель", 90), ("мясо", "Мясо по-французски", 120),
            ("напиток", "Чай черный", 15), ("напиток", "Кофе 3 в 1", 30), 
            ("напиток", "Компот", 25), ("напиток", "Сок", 30),
        ],
        "Четверг": [
            ("завтрак", "Блины", 60), ("завтрак", "Блины с творогом", 90), ("завтрак", "Омлет", 120),
            ("салат", "Мимоза", 90), ("салат", "Свежая капуста", 70),
            ("первое", "Гороховый", 70),
            ("гарнир", "Рис", 70), ("гарнир", "Греча", 70), ("гарнир", "Макароны", 70), 
            ("гарнир", "Пюре", 70), ("гарнир", "Капуста тушеная", 70), 
            ("мясо", "Картошка тушеная", 120), ("мясо", "Котлеты куриные", 90), 
            ("мясо", "Котлеты пожарские", 90), ("мясо", "Котлеты рыбные", 90), 
            ("мясо", "Рыба жареная", 100), ("мясо", "Ежики", 70), 
            ("мясо", "Шницель", 120), ("мясо", "Мясо по-французски", 150), ("мясо", "Печень", 120),
            ("напиток", "Чай черный", 15), ("напиток", "Кофе 3 в 1", 30), 
            ("напиток", "Кисель", 25), ("напиток", "Сок", 30),
        ],
        "Пятница": [
            ("завтрак", "Сырники", 100),
            ("салат", "Овощной", 80), ("салат", "Крабовый", 90),
            ("первое", "Солянка", 70),
            ("гарнир", "Рис", 70), ("гарнир", "Греча", 70), ("гарнир", "Макароны", 70), 
            ("гарнир", "Пюре", 70), ("гарнир", "Капуста тушеная", 70),
            ("мясо", "Плов", 70), ("мясо", "Котлеты куриные", 120), ("мясо", "Котлеты свиные", 90), 
            ("мясо", "Гуляш", 90), ("мясо", "Мясо по-французски", 140), 
            ("мясо", "Шницель", 150), ("мясо", "Ежики", 120), 
            ("мясо", "Голубцы", 70), ("мясо", "Рыба (в кляре)", 90), ("мясо", "Котлеты рубленые", 120),
            ("напиток", "Чай черный", 15), ("напиток", "Кофе 3 в 1", 30), 
            ("напиток", "Компот", 25), ("напиток", "Сок", 30),
        ]
    }
    
    # Выпечка (добавил сюда Хлеб)
    bakery = [
        ("выпечка", "Хлеб", 4),
        ("выпечка", "Пирог с луком и яйцом", 40), ("выпечка", "Конверт с творогом", 45), 
        ("выпечка", "Пирог с творогом", 45), ("выпечка", "Пирог картошка-грибы", 40), 
        ("выпечка", "Пирог с яблоком", 40), ("выпечка", "Пирог с повидлом", 45), 
        ("выпечка", "Слойка ветчина-сыр", 65), ("выпечка", "Пирог с капустой", 40), 
        ("выпечка", "Салами", 85), ("выпечка", "Турецкий", 90), ("выпечка", "Пицца с колбасой", 80), 
        ("выпечка", "Хот-дог", 75), ("выпечка", "Пицца сырно-чесночная", 75), 
        ("выпечка", "Пицца куриная", 85), ("выпечка", "Галета с курицей", 90), 
        ("выпечка", "Самса", 80), ("выпечка", "Сэндвич", 85)
    ]
    
    for day in menu:
        menu[day].extend(bakery)

    for day, items in menu.items():
        for cat, name, price in items:
            cur.execute(
                "INSERT INTO dishes (day, category, name, price) VALUES (?, ?, ?, ?)",
                (day, cat, name, price)
            )
            
    conn.commit()
    conn.close()

def get_dishes(day, category=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if category:
        cur.execute("SELECT name, price FROM dishes WHERE day=? AND category=?", (day, category))
    else:
        cur.execute("SELECT category, name, price FROM dishes WHERE day=?", (day,))
    result = cur.fetchall()
    conn.close()
    return result

def add_user(user_id, first_name, username):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, first_name, username) VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET first_name=excluded.first_name, username=excluded.username
    """, (user_id, first_name, username))
    conn.commit()
    conn.close()

def get_users_info(limit=50):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT first_name, username, user_id FROM users ORDER BY rowid DESC LIMIT ?", (limit,))
    result = cur.fetchall()
    conn.close()
    return result

def save_review(user_id, user_name, username, text):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    cur.execute("INSERT INTO reviews (user_id, user_name, username, text, date) VALUES (?, ?, ?, ?, ?)",
                (user_id, user_name, username, text, now))
    conn.commit()
    conn.close()

def get_reviews(limit=5):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, user_name, username, text, date FROM reviews ORDER BY id DESC LIMIT ?", (limit,))
    result = cur.fetchall()
    conn.close()
    return result

def delete_review(review_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM reviews WHERE id=?", (review_id,))
    conn.commit()
    conn.close()

def add_subscriber(user_id, reminder_time):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO subscribers (user_id, reminder_time) VALUES (?, ?)", (user_id, reminder_time))
    conn.commit()
    conn.close()

def remove_subscriber(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM subscribers WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_subscriber_time(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT reminder_time FROM subscribers WHERE user_id=?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def get_all_subscribers():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id, reminder_time FROM subscribers")
    result = cur.fetchall()
    conn.close()
    return result

def get_unique_users():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM subscribers UNION SELECT user_id FROM reviews UNION SELECT user_id FROM users")
    users = [row[0] for row in cur.fetchall()]
    conn.close()
    return users

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM reviews")
    reviews_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM subscribers")
    subs_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users")
    users_count = cur.fetchone()[0]
    conn.close()
    return users_count, reviews_count, subs_count

if __name__ == "__main__":
    init_db()
    print("База обновлена. Сегодня:", get_today_name())