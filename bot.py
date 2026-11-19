import telebot
from telebot import types
from config import TOKEN
from database import (
    init_db, get_dishes, get_today_name, get_tomorrow_name,
    save_review, get_reviews, delete_review,
    add_subscriber, remove_subscriber, get_subscriber_time, get_all_subscribers,
    get_unique_users, get_stats, add_user, get_users_info
)
from itertools import product
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Включаем поддержку middleware до создания бота
telebot.apihelper.ENABLE_MIDDLEWARE = True

bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 5110503662

CATEGORIES = ["завтрак", "салат", "первое", "гарнир", "мясо", "напиток", "выпечка"]
CATEGORY_EMOJI = {
    "завтрак": "🍳", "салат": "🥗", "первое": "🍲",
    "гарнир": "🍚", "мясо": "🍗", "напиток": "☕", "выпечка": "🥐",
}

user_budgets = {}
user_choices = {}

MAIN_BUTTONS = [
    "🍽 Меню на сегодня", "📅 Меню на завтра", 
    "💰 До суммы", "🧩 Собрать комбо",
    "⭐ Оставить отзыв", "📖 Читать отзывы",
    "🔔 Напоминание"
]

# ---------- Middleware (автосохранение юзеров) ----------
@bot.middleware_handler(update_types=['message'])
def track_user(bot_instance, message):
    if message.from_user:
        add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)

# ---------- Вспомогательные функции ----------
def is_weekend(day):
    return day in ["Суббота", "Воскресенье"]

def format_menu(day):
    if is_weekend(day):
        return f"😴 *{day}*. Столовая не работает. Отдыхаем!"
    if not get_dishes(day):
        return f"😔 На *{day.lower()}* меню пока нет."
    text = f"🍽 *Меню столовой на {day.lower()}*\n\n"
    for cat in CATEGORIES:
        dishes = get_dishes(day, cat)
        if not dishes: continue
        text += f"{CATEGORY_EMOJI[cat]} *{cat.capitalize()}*\n"
        for name, price in dishes:
            text += f"• {name} — {price} ₽\n"
        text += "\n"
    return text

def find_combos(day, categories, budget=None, limit=None):
    if is_weekend(day): return []
    dishes_by_cat = [get_dishes(day, cat) for cat in categories]
    if any(len(lst) == 0 for lst in dishes_by_cat): return []
    combos = []
    for combo in product(*dishes_by_cat):
        total = sum(item[1] for item in combo)
        if budget is None or total <= budget:
            combos.append((combo, total))
    combos.sort(key=lambda x: x[1], reverse=True)
    return combos[:limit] if limit else combos

def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(MAIN_BUTTONS[0]), types.KeyboardButton(MAIN_BUTTONS[1]))
    kb.add(types.KeyboardButton(MAIN_BUTTONS[2]), types.KeyboardButton(MAIN_BUTTONS[3]))
    kb.add(types.KeyboardButton(MAIN_BUTTONS[4]), types.KeyboardButton(MAIN_BUTTONS[5]))
    kb.add(types.KeyboardButton(MAIN_BUTTONS[6]))
    return kb

def get_combo_keyboard(user_id):
    chosen = user_choices.get(user_id, ["первое", "гарнир", "мясо", "напиток"])
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for cat in ["первое", "гарнир", "мясо", "салат", "напиток", "выпечка"]:
        mark = "✅ " if cat in chosen else "❌ "
        buttons.append(types.InlineKeyboardButton(f"{mark}{cat.capitalize()}", callback_data=f"toggle_{cat}"))
    kb.add(*buttons)
    kb.add(types.InlineKeyboardButton("Готово ▶️", callback_data="done_combo"))
    return kb

def send_long_message(chat_id, text, reply_markup=None):
    if len(text) <= 4000:
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=reply_markup)
        return
    parts = []
    while len(text) > 4000:
        split_idx = text.rfind('\n', 0, 4000)
        if split_idx == -1: split_idx = 4000
        parts.append(text[:split_idx])
        text = "🧩 *Продолжение:*\n\n" + text[split_idx:]
    parts.append(text)
    for i, part in enumerate(parts):
        markup = reply_markup if i == len(parts) - 1 else None
        bot.send_message(chat_id, part, parse_mode="Markdown", reply_markup=markup)

# ---------- Фоновая рассылка ----------
def send_lunch_reminder():
    current_time = datetime.now().strftime("%H:%M")
    today = get_today_name()
    if is_weekend(today) or not get_dishes(today): return
    subscribers = get_all_subscribers()
    text = (
        f"🔔 *Напоминание об обеде ({current_time})!*\n\n"
        "Самое время заглянуть в столовую. Сегодня в меню есть вкусные блюда!\n\n"
        "Нажми /menu, чтобы посмотреть меню, или /budget, чтобы подобрать обед."
    )
    for user_id, reminder_time in subscribers:
        if reminder_time == current_time:
            try:
                bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=main_keyboard())
            except Exception as e:
                print(f"Не удалось отправить {user_id}: {e}")

# ---------- АДМИН-ПАНЕЛЬ ----------

@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора.")
        return
        
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📊 Статистика бота", callback_data="admin_stats"))
    kb.add(types.InlineKeyboardButton("👥 Список пользователей", callback_data="admin_users"))
    kb.add(types.InlineKeyboardButton("📢 Сделать рассылку", callback_data="admin_broadcast"))
    
    bot.send_message(
        message.chat.id, 
        "👑 *Админ-панель*\n\nВыбери действие:", 
        parse_mode="Markdown", 
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def handle_admin_actions(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Нет доступа! ❌")
        return
        
    action = call.data.split("_")[1]
    
    if action == "stats":
        users, reviews, subs = get_stats()
        text = (
            "📊 *Статистика проекта:*\n\n"
            f"👥 Всего пользователей: *{users}*\n"
            f"⭐ Всего отзывов: *{reviews}*\n"
            f"🔔 Подписано на напоминания: *{subs}*\n"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

    elif action == "users":
        users = get_users_info(50)
        if not users:
            bot.answer_callback_query(call.id, "Пользователей пока нет.")
            return
            
        text = "👥 *Последние 50 пользователей:*\n\n"
        for name, username, uid in users:
            username_str = f"@{username}" if username else "без юзернейма"
            text += f"• {name} ({username_str}) — `{uid}`\n"
            
        bot.answer_callback_query(call.id)
        send_long_message(call.message.chat.id, text)
        
    elif action == "broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📢 Напиши текст, который нужно отправить ВСЕМ пользователям:")
        bot.register_next_step_handler(msg, send_broadcast_message)

def send_broadcast_message(message):
    if message.from_user.id != ADMIN_ID: return
    text_to_send = message.text
    users = get_unique_users()
    success_count = 0
    status_msg = bot.send_message(message.chat.id, "⏳ Начинаю рассылку...")
    
    for user_id in users:
        try:
            bot.send_message(user_id, text_to_send, parse_mode="Markdown")
            success_count += 1
        except Exception:
            pass 
            
    bot.edit_message_text(
        text=f"✅ *Рассылка завершена!*\n\nДоставлено: {success_count} из {len(users)} пользователей.",
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        parse_mode="Markdown"
    )

# ---------- Обычные команды ----------

@bot.message_handler(commands=["start"])
def cmd_start(message):
    text = f"Привет, {message.from_user.first_name}! 👋\nСегодня *{get_today_name()}*. Покажу меню и помогу собрать обед."
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_keyboard())

@bot.message_handler(commands=["menu"])
@bot.message_handler(func=lambda m: m.text == MAIN_BUTTONS[0])
def cmd_menu(message):
    bot.send_message(message.chat.id, format_menu(get_today_name()), parse_mode="Markdown")

@bot.message_handler(commands=["tomorrow"])
@bot.message_handler(func=lambda m: m.text == MAIN_BUTTONS[1])
def cmd_tomorrow(message):
    bot.send_message(message.chat.id, format_menu(get_tomorrow_name()), parse_mode="Markdown")

# ---------- Напоминания ----------

@bot.message_handler(commands=["reminder"])
@bot.message_handler(func=lambda m: m.text == "🔔 Напоминание")
def cmd_reminder(message):
    if is_weekend(get_today_name()):
        bot.send_message(message.chat.id, "Сегодня выходной, столовая не работает. Напоминание можно настроить на будни.")
    user_id = message.from_user.id
    current_time = get_subscriber_time(user_id)
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("11:20 (Большая перемена)", callback_data="time_11:20"))
    kb.add(types.InlineKeyboardButton("12:00", callback_data="time_12:00"))
    kb.add(types.InlineKeyboardButton("13:00", callback_data="time_13:00"))
    kb.add(types.InlineKeyboardButton("✍️ Свое время", callback_data="time_custom"))
    
    if current_time:
        text = f"🔔 У тебя включено напоминание на *{current_time}*.\nХочешь изменить время или отключить?"
        kb.add(types.InlineKeyboardButton("❌ Отключить напоминание", callback_data="time_off"))
    else:
        text = "Выбери удобное время, когда я буду напоминать тебе про обед (по будням):"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def handle_time_choice(call):
    user_id = call.from_user.id
    choice = call.data.split("_")[1]
    if choice == "off":
        remove_subscriber(user_id)
        bot.edit_message_text("🔕 Напоминания отключены.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif choice == "custom":
        msg = bot.send_message(call.message.chat.id, "Напиши время в формате *ЧЧ:ММ* (например, `11:45`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_custom_time)
    else:
        add_subscriber(user_id, choice)
        bot.edit_message_text(f"🔔 Отлично! Буду напоминать тебе каждый день в *{choice}*.", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")

def save_custom_time(message):
    if message.text in MAIN_BUTTONS: return
    time_str = message.text.strip()
    try:
        datetime.strptime(time_str, "%H:%M")
        add_subscriber(message.from_user.id, time_str)
        bot.send_message(message.chat.id, f"🔔 Отлично! Буду напоминать тебе каждый день в *{time_str}*.", parse_mode="Markdown", reply_markup=main_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат. Напиши именно так: `11:20`", parse_mode="Markdown", reply_markup=main_keyboard())

# ---------- Бюджет ----------

@bot.message_handler(commands=["budget"])
@bot.message_handler(func=lambda m: m.text == MAIN_BUTTONS[2])
def cmd_budget(message):
    if is_weekend(get_today_name()):
        bot.send_message(message.chat.id, "Сегодня выходной, столовая не работает. Ждем тебя в понедельник!")
        return
    msg = bot.send_message(message.chat.id, "Введи максимальную сумму в рублях (например, 200):")
    bot.register_next_step_handler(msg, budget_step)

def budget_step(message):
    if message.text in MAIN_BUTTONS: return
    try:
        budget = int(message.text)
        if budget <= 0: raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Нужно целое число больше нуля.")
        return
    user_budgets[message.from_user.id] = budget
    user_choices[message.from_user.id] = ["первое", "гарнир", "мясо", "напиток"]
    bot.send_message(message.chat.id, f"Бюджет: *{budget} ₽*. Нажми на категории и «Готово»:", parse_mode="Markdown", reply_markup=get_combo_keyboard(message.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def toggle_category(call):
    cat = call.data.split("_")[1]
    user_id = call.from_user.id
    if user_id not in user_choices: user_choices[user_id] = ["первое", "гарнир", "мясо", "напиток"]
    chosen = user_choices[user_id]
    if cat in chosen: chosen.remove(cat)
    else: chosen.append(cat)
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_combo_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: call.data == "done_combo")
def done_combo(call):
    user_id = call.from_user.id
    budget = user_budgets.get(user_id, 200)
    chosen = user_choices.get(user_id, [])
    if not chosen:
        bot.answer_callback_query(call.id, "Выбери хотя бы одну категорию! ❌")
        return
    bot.answer_callback_query(call.id, "Ищу...")
    combos = find_combos(get_today_name(), chosen, budget=budget, limit=None)
    if not combos:
        bot.edit_message_text(f"На {budget} ₽ ничего не влезает 😔", chat_id=call.message.chat.id, message_id=call.message.message_id)
        return
    text = f"💰 *Что можно взять на {budget} ₽*\n_Найдено: {len(combos)}_\n\n"
    for i, (combo, total) in enumerate(combos, 1):
        text += f"*{i}. ({total} ₽)*\n"
        for name, price in combo: text += f"• {name} — {price} ₽\n"
        text += f"_Остаток: {budget - total} ₽_\n\n"
    send_long_message(call.message.chat.id, text)

# ---------- Собрать комбо ----------

@bot.message_handler(commands=["combo"])
@bot.message_handler(func=lambda m: m.text == MAIN_BUTTONS[3])
def cmd_combo(message):
    if is_weekend(get_today_name()):
        bot.send_message(message.chat.id, "Сегодня выходной, столовая не работает. Ждем тебя в понедельник!")
        return
    msg = bot.send_message(message.chat.id, "Напиши категории через запятую (например, `первое, гарнир, мясо`):")
    bot.register_next_step_handler(msg, combo_step)

def combo_step(message):
    if message.text in MAIN_BUTTONS: return
    chosen = [c for c in message.text.lower().replace(" ", "").split(",") if c in CATEGORIES]
    if not chosen:
        bot.send_message(message.chat.id, "Не понял категории 😕")
        return
    combos = find_combos(get_today_name(), chosen, budget=None, limit=None)
    text = f"🧩 *Найдено комбо: {len(combos)}*\n\n"
    for i, (combo, total) in enumerate(combos, 1):
        text += f"*{i}. ({total} ₽)*\n"
        for name, price in combo: text += f"• {name} — {price} ₽\n"
        text += "\n"
    send_long_message(message.chat.id, text)

# ---------- Отзывы ----------

@bot.message_handler(commands=["review"])
@bot.message_handler(func=lambda m: m.text == MAIN_BUTTONS[4])
def cmd_review(message):
    msg = bot.send_message(message.chat.id, "Напиши свой отзыв:")
    bot.register_next_step_handler(msg, save_review_step)

def save_review_step(message):
    if message.text in MAIN_BUTTONS: return
    save_review(message.from_user.id, message.from_user.first_name, f"@{message.from_user.username}" if message.from_user.username else "", message.text)
    bot.send_message(message.chat.id, "Спасибо за отзыв! ⭐", reply_markup=main_keyboard())

@bot.message_handler(commands=["reviews"])
@bot.message_handler(func=lambda m: m.text == MAIN_BUTTONS[5])
def cmd_read_reviews(message):
    reviews = get_reviews(5)
    if not reviews:
        bot.send_message(message.chat.id, "Пока нет отзывов. Будь первым!", reply_markup=main_keyboard())
        return
    text = "📖 *Последние отзывы:*\n\n"
    kb = types.InlineKeyboardMarkup(row_width=1)
    for rev_id, user_id, name, username, review_text, date in reviews:
        text += f"👤 *{name}* ({username})\n"
        text += f"_{date}_\n"
        text += f"«{review_text}»\n\n"
        if user_id == message.from_user.id or message.from_user.id == ADMIN_ID:
            kb.add(types.InlineKeyboardButton(f"🗑 Удалить отзыв от {date}", callback_data=f"del_rev_{rev_id}"))
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_rev_"))
def handle_delete_review(call):
    rev_id = call.data.split("_")[2]
    delete_review(rev_id)
    bot.answer_callback_query(call.id, "Отзыв удален 🗑")
    bot.edit_message_text(
        text="🗑 *Отзыв успешно удален.*\n\nНажми «📖 Читать отзывы», чтобы обновить список.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown"
    )

# ---------- Запуск ----------
if __name__ == "__main__":
    from requests.exceptions import RequestException
    import time
    init_db()
    print(f"Бот запущен. Сегодня: {get_today_name()}")
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_lunch_reminder, 'cron', second=0) 
    scheduler.start()
    print("Планировщик напоминаний запущен.")
    while True:
        try:
            bot.infinity_polling(timeout=90, long_polling_timeout=5)
        except RequestException:
            print("⚠️ Ошибка соединения. Перезапуск через 15 секунд...")
            time.sleep(15)