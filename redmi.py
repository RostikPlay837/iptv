import logging
import sqlite3
import json
import random
import sys
import asyncio
import time
import os
import subprocess
import re
import shutil
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.error import TelegramError, NetworkError, TimedOut

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8870027289:AAEVJPMOw5EIy2bZn4Jkc7gIO4U3Fdh2uhg"
BOT_VERSION = "2.1"

# Админы
ADMIN_IDS = [
    5257003639,  # @tixconoff
    1338974901   # @basya_tech
]

# Игнорируемые ID
IGNORED_USERS = [777000]
IGNORED_USERNAMES = ["GroupAnonymousBot", "channel_bot"]

BROADCAST_FILE = "broadcasted_chats.json"
SHOP_PAGE_SIZE = 10

# Глобальные переменные
_stop_event = asyncio.Event()
_last_battery_warning_time = {}
_bot_start_time = time.time()
_awaiting_gif = {}
_last_redmi_time = {}
REDMI_COOLDOWN = 10
_sys_cache = None
_sys_cache_time = 0
SYS_CACHE_TTL = 5

# Ачивки
ACHIEVEMENTS = {
    1: "Первый клик",
    10: "Десятник",
    50: "Половинный кликер",
    100: "Сотник",
    500: "Пятисотка",
    1000: "Тысячник",
    5000: "Пятитысячный",
    10000: "Десятитысячный долбоёб",
    25000: "Двадцатипятитысячный мудак",
    50000: "Пятидесятитысячный еблан",
    100000: "Стотысячный говноед"
}

# Магазин титулов
SHOP_TITLES = {
    "🍆 Ебатор": 30,
    "💩 Говноед": 30,
    "🤡 Клоун кликов": 30,
    "🔥 Пидор кликов": 30,
    "💀 Мразь кликовая": 30,
    "👑 Король лохов": 30,
    "🧠 Дебил кликов": 30,
    "😈 Демон хуйни": 30,
    "🚀 Ебанутый кликер": 30,
    "💪 Лох с кликами": 30,
    "🦁 Ебаный лев": 35,
    "🐉 Дракон гандонов": 35,
    "👹 Бес ебучий": 35,
    "💎 Алмазный пидор": 35,
    "🌟 Звездный лох": 35,
    "🔥 Пламенный даун": 35,
    "💀 Некромант хуйни": 40,
    "🧙 Маг говна": 40,
    "⚔️ Воин пидоров": 40,
    "🛡️ Защитник лохов": 40,
    "👽 Пришелец ебаный": 45,
    "🤖 Робот мусора": 45,
    "🎪 Клоун ебучий": 45,
    "👻 Призрак пидора": 45,
    "🧛 Вампир кликов": 50,
    "🐺 Оборотень хуйни": 50,
    "🧟 Зомби ебаный": 50,
    "👾 Инопланетный уёбок": 50,
    "🤡 Джокер говна": 55,
    "💣 Терминатор пидоров": 55,
    "👑 Император лохов": 60,
    "⚡ Бог ебаный": 60,
    "🔥 Титан хуйни": 60,
    "💀 Легенда гандонов": 65,
    "🌟 Миф пидоров": 65,
    "👹 Дьявол мусора": 70,
    "😇 Ангел хуйни": 70,
    "🚀 Космический ебанат": 75,
    "💎 Бесконечный пидор": 80,
    "♾️ Бессмертный лох": 100
}
GIF_PRICE = 250

# Оскорбления для кликов
INSULTS_CLICK = [
    "Ты чё, долбоёб, кликаешь как ненормальный?",
    "Очередной клик, а ты всё такой же уёбок.",
    "Молодец, ещё один клик, теперь ты чуть менее бесполезен.",
    "Кликай-кликай, всё равно ты ничтожество.",
    "Твои клики не спасут мир, но хотя бы тебя развлекают, дебил.",
    "А ты реально считаешь, что это имеет значение? Иди нахуй.",
    "Ещё клик, и ты станешь чуть ближе к тому, чтобы я тебя забанил. Шучу, мне похуй.",
    "Поздравляю, ты кликнул. Ты думал, это что-то изменит? Нет, ты всё ещё лох.",
    "Клик принят. Твоя жизнь от этого не станет лучше, но хотя бы ты занят делом.",
    "Ещё один клик – и я вырублю сервер, мне похуй.",
    "Зачем ты это делаешь? У тебя что, заняться нечем? А, ну да, редми го – вот и всё твоё богатство.",
    "Ты реально думаешь, что я считаю эти клики? Мне насрать, но бот считает.",
    "Клик! Ты на шаг ближе к тому, чтобы я тебя забанил. Шучу, мне похуй на тебя.",
    "Очередной бесполезный клик от очередного бесполезного человека.",
    "Кликай, кликай... Может, когда-нибудь ты станешь полезным. Хотя вряд ли.",
    "Мне кажется, или ты реально дебил, который кликает просто так?",
    "Ещё клик – и я отправлю тебя в игнор. А хотя нет, мне похуй.",
    "Клики не сделают тебя лучше, но хотя бы займут твоё пустое время.",
    "Поздравляю, ты только что потратил 0.5 секунды своей жизни на клик. Гордись.",
    "Клик – и ты всё такой же никчёмный. Но бот рад, ему похуй.",
    "Ты кликаешь как будто от этого зависит твоя жизнь. Спойлер: нет.",
    "Ещё клик, и я начну уважать тебя. Шучу, не начну.",
    "Кликай, пока редми го не взорвался!",
    "Твои клики такие же бесполезные, как и ты сам.",
    "Я считаю твои клики, хотя мне глубоко насрать.",
    "О, опять этот клоун кликает...",
    "Клик! А теперь иди нахуй!",
    "Ты реально считаешь, что кто-то оценит твои клики? Нет.",
    "Кликай, кликай... Всё равно ты никто.",
    "Ты думаешь, эти клики тебя спасут? Нет, ты просто теряешь время.",
    "Очередной клик от очередного неудачника.",
    "Мне кажется, ты кликаешь быстрее, чем соображаешь.",
    "Кликни ещё раз, может быть, станешь умнее? Не станешь."
]

# Оскорбления при ачивке
INSULTS_ACHIEVE = [
    "И ты ещё радуешься, как будто что-то добился. Поздравляю, ты всё ещё лох.",
    "Ачивка? Серьёзно? Ты идиот? Ну ладно, держи свою звёздочку.",
    "Ура, ты получил ачивку. Только это ничего не меняет, ты всё ещё никто.",
    "Ещё одна ачивка в коллекцию твоих бесполезных достижений.",
    "Поздравляю, ты теперь официально задрот. Ачивка получена.",
    "Ты реально думал, что я скажу что-то хорошее? Ачивка есть, а ума нет.",
    "О, ты получил ачивку. Мне насрать, но бот говорит 'молодец'.",
    "Ачивка! Теперь ты официально заслужил звание 'ещё один лох с ачивкой'.",
    "Поздравляю! Ты потратил кучу времени на клики ради этой ачивки. Зачем?",
    "Ачивка получена. Ты серьёзно думаешь, что это кого-то волнует?",
    "Ты серьёзно радуешься ачивке? У тебя что, жизни нет?",
    "Ачивка! Как будто это что-то меняет. Ты всё ещё лох.",
    "Поздравляю с ачивкой, лох!",
    "Ещё одна бесполезная ачивка для бесполезного человека.",
    "Ачивка есть, а мозгов нет.",
    "Ты получил ачивку. И что дальше? Ничего.",
    "Поздравляю! Теперь ты можешь похвастаться перед другими лохами.",
    "Ачивка получена. Надеюсь, ты доволен собой, потому что я нет.",
    "Ты реально гордишься этим? Серьёзно?",
    "Ещё одна ачивка, которая ничего не значит."
]

# Рандомные надписи для /redmi
RANDOM_REDMI_MESSAGES = [
    "И всё это говно работает на древнем редми го, который скоро взорвётся! 💥",
    "Хост: Redmi Go. Процессор: Snapdragon 425. 1 ГБ ОЗУ — мне похуй на память. 😂",
    "Кто вообще додумался хостить бота на редми го? Только ебанутые на всю голову! 🧠",
    "Redmi Go: 8 ГБ памяти, 1 ГБ ОЗУ — греется как чайник, тормозит как улитка, но работает! Чудо! 🔥",
    "Процессор: Snapdragon 425 (4 ядра по 1.4 ГГц). 8 ГБ памяти, 1 ГБ ОЗУ. Мощности хватает только чтобы считать твои клики, лох!",
    "Этот бот держится на честном слове и мате. Хост вот-вот сдохнет, но мне похуй!",
    "Redmi Go: производительность как у калькулятора, но бот работает! Назло всем! 😈",
    "Хостишь бота на редми го? Ты либо гений, либо долбоёб. Скорее второе. 🤡",
    "Технические характеристики: 8 ГБ памяти, 1 ГБ ОЗУ, старый, медленный, но упорный. Как твой бывший! 😂",
    "Всё, что нужно для счастья: Redmi Go, интернет и отсутствие мозгов у хозяина!",
    "Если Redmi Go взорвётся — я предупреждал. Но бота перезапустить не забудьте, лохи!",
    "Хост работает на батарейке от микроволновки и волевых усилиях разработчика. Кто бы сомневался!",
    "Кто придумал хостить на Redmi Go? Таких нужно в психушку отправлять, а не ботов писать! 🏥",
    "Redmi Go: 1 ГБ ОЗУ хватит всем! Шучу, никому не хватит. 🤡",
    "8 ГБ встроенной памяти? Да там только мемы с котиками!",
    "Android 11 на Redmi Go? Вы ебанутые! Но оно работает! 🚀",
    "Хост работает на минималках, но ты всё равно не догонишь!",
    "Redmi Go — это легенда, которая скоро превратится в пыль.",
    "Этот бот — единственное, что работает на этом телефоне без ошибок.",
    "Скорость работы прямо пропорциональна количеству выпитого у хозяина.",
    "Если бот тормозит — значит, Redmi Go перегревается. Или хозяин перегрелся.",
    "8 ГБ памяти, 1 ГБ ОЗУ — как ты вообще это запустил? Чудо инженерии!",
    "Redmi Go на Android 11 — это как космический корабль на дровах, но летит!",
    "1 ГБ ОЗУ? Да там даже кеш телеграма не влезает, а бот работает!",
    "Snapdragon 425, 8 ГБ памяти — это уровень микроволновки, но мы справляемся!"
]

# Рандомные сообщения для спама о разряде батареи
BATTERY_WARNING_MESSAGES = [
    "⚠️ ВНИМАНИЕ, ДОЛБОЁБЫ! ⚠️\n\nБатарея на Redmi Go упала до {level}%!\n{status}\nТемпература: {temp}°C\n\nХост вот-вот сдохнет, если кто-то не поставит эту залупу на зарядку! 🖕\n\nP.S. Разраб - даун, забыл зарядить телефон!\n\n🔕 Чтобы отключить эти уведомления - используй /notify",
    "🔴 ТРЕВОГА, ПИДОРЫ! 🔴\n\nБатарея {level}%! Хост на грани смерти!\n{status}\nТемпература: {temp}°C\n\nКто-нибудь, поставьте Redmi Go на зарядку, пока я не вырубился нахуй! ⚡\n\nP.S. Хозяин - ебанутый, не следит за батареей!\n\n🔕 Чтобы отключить эти уведомления - используй /notify",
    "💀 ВСЁ, ПИЗДЕЦ! 💀\n\nБатарея {level}%! Скоро вырублюсь!\n{status}\nТемпература: {temp}°C\n\nЕсли не хотите потерять бота - тащите зарядку! 🖕\n\nP.S. Разработчик - мудак, не поставил напоминалку!\n\n🔕 Чтобы отключить эти уведомления - используй /notify",
    "🤬 СУКА, РАЗРЯЖАЮСЬ! 🤬\n\nБатарея {level}%!\n{status}\nТемпература: {temp}°C\n\nЯ сейчас выключусь, и все ваши клики пойдут нахуй!\n\nP.S. Идите нахуй, лохи!\n\n🔕 Чтобы отключить эти уведомления - используй /notify",
    "⚡ БАТАРЕЯ ПИЗДЕЦ! ⚡\n\n{level}% осталось!\n{status}\nТемпература: {temp}°C\n\nСтавьте на зарядку, пока я не сдох! 🖕\n\nP.S. Ебаный Redmi Go...\n\n🔕 Чтобы отключить эти уведомления - используй /notify",
    "🔥 ГОРИМ, ПИДОРЫ! 🔥\n\nБатарея {level}%!\n{status}\nТемпература: {temp}°C\n\nХост вот-вот вырубится! Тащите зарядку!\n\nP.S. Разраб - конченый, не уследил!\n\n🔕 Чтобы отключить эти уведомления - используй /notify",
    "💢 АЛО, ДАУНЫ! 💢\n\nБатарея {level}%!\n{status}\nТемпература: {temp}°C\n\nКто-нибудь, поставьте на зарядку эту бандуру!\n\nP.S. Я устал от этого Redmi Go...\n\n🔕 Чтобы отключить эти уведомления - используй /notify",
    "🪫 ВНИМАНИЕ! 🪫\n\nБатарея {level}%!\n{status}\nТемпература: {temp}°C\n\nЕсли бот вырубится - я вас всех запомню! 🖕\n\nP.S. Идите нахуй, лошары!\n\n🔕 Чтобы отключить эти уведомления - используй /notify",
    "📢 СООБЩЕНИЕ ДЛЯ ЛОХОВ! 📢\n\nБатарея {level}%!\n{status}\nТемпература: {temp}°C\n\nСтавьте на зарядку, пока я не сдох!\n\nP.S. Разработчик - даун, забыл зарядить!\n\n🔕 Чтобы отключить эти уведомления - используй /notify",
    "⚠️ ТЫ ЧЁ, ДОЛБОЁБ? ⚠️\n\nБатарея {level}%!\n{status}\nТемпература: {temp}°C\n\nПоставь на зарядку, пока я не вырубился!\n\nP.S. Ебаный в рот этот Redmi Go!\n\n🔕 Чтобы отключить эти уведомления - используй /notify"
]

# Админ-функции
ADMIN_FUNCTIONS = {
    "📢 Сказать всем": "admin_broadcast",
    "👑 Выдать титул": "admin_give_title",
    "🏆 Выдать ачивку": "admin_give_achievement",
    "🔨 Забанить лоха": "admin_ban",
    "🔓 Разбанить лоха": "admin_unban",
    "📊 Статистика": "admin_stats",
    "📝 Сменить статус": "admin_status",
    "🎭 Сменить ник": "admin_change_nick",
    "👥 Все игроки": "admin_players",
    "➕ Добавить админа": "admin_addadmin"
}

def load_broadcasted_chats():
    try:
        with open(BROADCAST_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_broadcasted_chats(chats):
    with open(BROADCAST_FILE, 'w') as f:
        json.dump(list(chats), f)

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_ignored_user(user):
    if user is None:
        return True
    if user.id in IGNORED_USERS:
        return True
    if user.username and user.username in IGNORED_USERNAMES:
        return True
    return False

def get_uptime():
    elapsed = int(time.time() - _bot_start_time)
    days = elapsed // 86400
    hours = (elapsed % 86400) // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60
    parts = []
    if days > 0:
        parts.append(f"{days}д")
    if hours > 0:
        parts.append(f"{hours}ч")
    if minutes > 0:
        parts.append(f"{minutes}м")
    parts.append(f"{seconds}с")
    return " ".join(parts)

# ------------------- МИГРАЦИЯ БД -------------------
def init_db():
    try:
        conn = sqlite3.connect('clicks.db')
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cur.fetchall()]
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                clicks INTEGER DEFAULT 0,
                achievements TEXT DEFAULT '[]',
                title TEXT DEFAULT 'Без титула',
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                status TEXT DEFAULT 'Живой',
                banned INTEGER DEFAULT 0,
                notify_enabled INTEGER DEFAULT 1
            )
        ''')
        if 'title' not in columns:
            cur.execute('ALTER TABLE users ADD COLUMN title TEXT DEFAULT "Без титула"')
        if 'username' not in columns:
            cur.execute('ALTER TABLE users ADD COLUMN username TEXT DEFAULT ""')
        if 'first_name' not in columns:
            cur.execute('ALTER TABLE users ADD COLUMN first_name TEXT DEFAULT ""')
        if 'status' not in columns:
            cur.execute('ALTER TABLE users ADD COLUMN status TEXT DEFAULT "Живой"')
        if 'banned' not in columns:
            cur.execute('ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0')
        if 'notify_enabled' not in columns:
            cur.execute('ALTER TABLE users ADD COLUMN notify_enabled INTEGER DEFAULT 1')
        conn.commit()
        conn.close()
        logger.info("База данных инициализирована/обновлена")
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")

def get_user_data(user_id):
    try:
        conn = sqlite3.connect('clicks.db')
        cur = conn.cursor()
        cur.execute('SELECT clicks, achievements, title, username, first_name, status, banned, notify_enabled FROM users WHERE user_id = ?', (user_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                'clicks': row[0],
                'achievements': json.loads(row[1]) if row[1] else [],
                'title': row[2] if row[2] else "Без титула",
                'username': row[3] if row[3] else "",
                'first_name': row[4] if row[4] else "",
                'status': row[5] if row[5] else "Живой",
                'banned': row[6] if row[6] else 0,
                'notify_enabled': row[7] if row[7] is not None else 1
            }
        return None
    except Exception as e:
        logger.error(f"Ошибка получения данных: {e}")
        return None

def save_user_data(user_id, clicks, achievements, title, username, first_name, status="Живой", banned=0, notify_enabled=1):
    try:
        conn = sqlite3.connect('clicks.db')
        cur = conn.cursor()
        cur.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, clicks, achievements, title, username, first_name, status, banned, notify_enabled) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, clicks, json.dumps(achievements), title, username, first_name, status, banned, notify_enabled))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения данных: {e}")
        return False

# ------------------- СИСТЕМНАЯ ИНФОРМАЦИЯ (КЕШИРОВАННАЯ) -------------------
def get_cpu_usage():
    try:
        with open('/proc/stat', 'r') as f:
            stat1 = f.readline().split()
        time.sleep(0.1)
        with open('/proc/stat', 'r') as f:
            stat2 = f.readline().split()
        user1, nice1, system1, idle1 = int(stat1[1]), int(stat1[2]), int(stat1[3]), int(stat1[4])
        user2, nice2, system2, idle2 = int(stat2[1]), int(stat2[2]), int(stat2[3]), int(stat2[4])
        total1 = user1 + nice1 + system1 + idle1
        total2 = user2 + nice2 + system2 + idle2
        idle = idle2 - idle1
        total = total2 - total1
        if total == 0:
            return random.randint(5, 30)
        usage = (1 - idle / total) * 100
        if usage > 100:
            usage = 100
        return round(usage, 1)
    except:
        return random.randint(5, 30)

def get_cpu_freq_mhz():
    try:
        for cpu in range(0, 4):
            path = f'/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_cur_freq'
            if os.path.exists(path):
                with open(path, 'r') as f:
                    freq_khz = int(f.read().strip())
                    if freq_khz > 0:
                        return round(freq_khz / 1000, 0)
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'MHz' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        return round(float(parts[1].strip()), 0)
        return random.randint(800, 1400)
    except:
        return random.randint(800, 1400)

def get_ram_info():
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        total_kb = int(re.search(r'MemTotal:\s+(\d+)', meminfo).group(1))
        avail_kb = int(re.search(r'MemAvailable:\s+(\d+)', meminfo).group(1))
        total_mb = round(total_kb / 1024, 0)
        used_mb = round((total_kb - avail_kb) / 1024, 0)
        free_mb = round(avail_kb / 1024, 0)
        percent = round(((total_kb - avail_kb) / total_kb) * 100, 1)
        return total_mb, used_mb, free_mb, percent
    except:
        try:
            output = subprocess.check_output(['free', '-m'], text=True, stderr=subprocess.DEVNULL)
            for line in output.split('\n'):
                if 'Mem:' in line:
                    parts = line.split()
                    total = int(parts[1])
                    used = int(parts[2])
                    free = int(parts[3]) if len(parts) > 3 else total - used
                    percent = round((used / total) * 100, 1)
                    return total, used, free, percent
        except:
            total = 1024  # 1 ГБ ОЗУ для Redmi Go
            used = random.randint(500, 900)
            free = total - used
            percent = round((used / total) * 100, 1)
            return total, used, free, percent

def get_battery_info():
    try:
        if shutil.which('termux-battery-status'):
            output = subprocess.check_output(['termux-battery-status'], text=True, stderr=subprocess.DEVNULL)
            data = json.loads(output)
            level = data.get('percentage', 0)
            status = data.get('status', 'UNKNOWN')
            temp = data.get('temperature', 0)
            if status == 'CHARGING':
                status_text = 'Заряжается'
                is_charging = True
            elif status == 'DISCHARGING':
                status_text = 'Разряжается'
                is_charging = False
            elif status == 'FULL':
                status_text = 'Полный'
                is_charging = True
            elif status == 'NOT_CHARGING':
                status_text = 'Не заряжается'
                is_charging = False
            else:
                status_text = 'Неизвестно'
                is_charging = False
            return level, status_text, is_charging, temp
    except:
        pass

    try:
        if shutil.which('dumpsys'):
            output = subprocess.check_output(['dumpsys', 'battery'], text=True, stderr=subprocess.DEVNULL)
            level = None
            status = None
            temp = None
            is_charging = False
            for line in output.split('\n'):
                if 'level' in line:
                    match = re.search(r'level:\s+(\d+)', line)
                    if match:
                        level = int(match.group(1))
                if 'status' in line:
                    match = re.search(r'status:\s+(\d+)', line)
                    if match:
                        code = int(match.group(1))
                        if code == 2:
                            status = 'Заряжается'
                            is_charging = True
                        elif code == 3:
                            status = 'Разряжается'
                            is_charging = False
                        elif code == 4:
                            status = 'Не заряжается'
                            is_charging = False
                        elif code == 5:
                            status = 'Полный'
                            is_charging = True
                        else:
                            status = 'Неизвестно'
                            is_charging = False
                if 'temperature' in line:
                    match = re.search(r'temperature:\s+(\d+)', line)
                    if match:
                        temp = int(match.group(1)) / 10
            if level is not None:
                if status is None:
                    status = 'Неизвестно'
                    is_charging = False
                if temp is None:
                    temp = round(random.uniform(25, 40), 1)
                return level, status, is_charging, temp
    except:
        pass

    try:
        level = None
        status = None
        temp = None
        is_charging = False
        for path in ['/sys/class/power_supply/battery/capacity', '/sys/class/power_supply/BAT0/capacity']:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    level = int(f.read().strip())
                break
        for path in ['/sys/class/power_supply/battery/status', '/sys/class/power_supply/BAT0/status']:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    st = f.read().strip()
                    if 'Charging' in st:
                        status = 'Заряжается'
                        is_charging = True
                    elif 'Discharging' in st:
                        status = 'Разряжается'
                        is_charging = False
                    elif 'Full' in st:
                        status = 'Полный'
                        is_charging = True
                    else:
                        status = st
                        is_charging = False
                break
        for path in ['/sys/class/power_supply/battery/temp', '/sys/class/power_supply/BAT0/temp']:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    temp = int(f.read().strip()) / 10
                break
        if level is not None:
            if status is None:
                status = 'Неизвестно'
                is_charging = False
            if temp is None:
                temp = round(random.uniform(25, 40), 1)
            return level, status, is_charging, temp
    except:
        pass

    level = random.randint(20, 95)
    status = random.choice(['Заряжается', 'Разряжается', 'Не заряжается'])
    is_charging = status == 'Заряжается'
    temp = round(random.uniform(25, 40), 1)
    return level, status, is_charging, temp

def get_cpu_temp():
    try:
        for path in ['/sys/class/thermal/thermal_zone0/temp', '/sys/class/thermal/thermal_zone1/temp']:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    temp = int(f.read().strip()) / 1000
                    return round(temp, 1)
        return round(random.uniform(30, 65), 1)
    except:
        return round(random.uniform(30, 65), 1)

def _get_system_info_sync():
    cpu = get_cpu_usage()
    cpu_freq = get_cpu_freq_mhz()
    ram_total, ram_used, ram_free, ram_percent = get_ram_info()
    battery_level, battery_status, is_charging, battery_temp = get_battery_info()
    cpu_temp = get_cpu_temp()
    return {
        'cpu_usage': cpu,
        'cpu_freq': cpu_freq,
        'ram_total_mb': ram_total,
        'ram_used_mb': ram_used,
        'ram_free_mb': ram_free,
        'ram_percent': ram_percent,
        'battery_percent': battery_level,
        'battery_status': battery_status,
        'battery_is_charging': is_charging,
        'battery_temp': battery_temp,
        'cpu_temp': cpu_temp
    }

async def get_system_info_async():
    global _sys_cache, _sys_cache_time
    now = time.time()
    if _sys_cache is not None and (now - _sys_cache_time) < SYS_CACHE_TTL:
        return _sys_cache
    info = await asyncio.to_thread(_get_system_info_sync)
    _sys_cache = info
    _sys_cache_time = now
    return info

# ------------------- ОЧИСТКА АНТИСПАМА -------------------
async def clean_redmi_history():
    while not _stop_event.is_set():
        await asyncio.sleep(300)
        now = time.time()
        to_delete = [uid for uid, t in _last_redmi_time.items() if now - t > 60]
        for uid in to_delete:
            del _last_redmi_time[uid]

# ------------------- КОМАНДЫ -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if is_ignored_user(user):
            return
        user_data = get_user_data(user.id)
        if not user_data:
            save_user_data(user.id, 0, [], "Без титула", user.username or "", user.first_name or "")
        if user_data and user_data.get('banned', 0) == 1:
            await update.message.reply_text("Ты забанен, лох! Иди нахуй! 🔨")
            return
        text = (
            f"🤬 ПРИВЕТ, ДОЛБОЁБ! 🤬\n\n"
            f"Я - бот для кликов на Redmi Go с Android 11.\n"
            f"Версия: {BOT_VERSION}\n\n"
            "📌 КОМАНДЫ:\n\n"
            "/click - кликнуть (мат + ачивки)\n"
            "/profile - твой профиль\n"
            "/top - топ-10 кликеров\n"
            "/shop - МАГАЗИН ТИТУЛОВ И ГИФОК (ТОЛЬКО В ЛИЧКЕ!)\n"
            "/redmi - информация о хосте + пинг + аптайм (антиспам 10 сек)\n"
            "/notify - включить/отключить уведомления о разряде батареи\n"
            "/changelog - список изменений\n"
            "/start - это сообщение\n\n"
            "💢 А ТЕПЕРЬ ИДИ НАХУЙ И КЛИКАЙ!"
        )
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")

async def changelog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if is_ignored_user(user):
            return
        if get_user_data(user.id) and get_user_data(user.id).get('banned', 0) == 1:
            await update.message.reply_text("Ты забанен! 🔨")
            return
        text = (
            "📋 **СПИСОК ИЗМЕНЕНИЙ (Версия 2.1)** 📋\n\n"
            "✅ **Магазин разделён на две категории:**\n"
            "   • Титулы (пагинация)\n"
            "   • Отправить гифку всем (250 кликов)\n\n"
            "✅ **Процесс отправки гифки:**\n"
            "   • Предупреждение о 18+\n"
            "   • Запрос гифки и текста\n"
            "   • Подтверждение и списание кликов\n"
            "   • Рассылка всем пользователям с подписью: 'Анонимный игрок за 250 кликов скинул это!'\n"
            "   • Админы получают лог с ID отправителя\n\n"
            "✅ **Бан/разбан через админ-панель:**\n"
            "   • /ban [ID] – забанить навсегда\n"
            "   • /unban [ID] – разбанить\n"
            "   • Забаненный не может кликать и совершать покупки\n\n"
            "✅ **Новые админы:** @tixconoff и @basya_tech\n"
            "✅ **Антиспам на /redmi – 10 секунд между вызовами** (для каждого игрока отдельно)\n"
            "✅ **Оптимизация производительности** – кеширование системной информации (5 секунд), асинхронный сбор данных\n"
            "✅ **Команда /backup (только @tixconoff)** – отправляет БД и JSON-файлы\n\n"
            "💢 **А ТЕПЕРЬ ИДИ НАХУЙ И КЛИКАЙ!** 🖕"
        )
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Ошибка в /changelog: {e}")

async def notify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if is_ignored_user(user):
            return
        user_data = get_user_data(user.id)
        if not user_data:
            await update.message.reply_text("Начни с /click, лох! А потом уже настраивай уведомления.")
            return
        if user_data.get('banned', 0) == 1:
            await update.message.reply_text("Ты забанен, лох! Иди нахуй! 🔨")
            return
        current = user_data.get('notify_enabled', 1)
        new_status = 0 if current == 1 else 1
        save_user_data(
            user.id,
            user_data['clicks'],
            user_data['achievements'],
            user_data['title'],
            user_data['username'],
            user_data['first_name'],
            user_data['status'],
            user_data['banned'],
            new_status
        )
        if new_status == 1:
            await update.message.reply_text("✅ Уведомления о разряде батареи **ВКЛЮЧЕНЫ**!\n\nТеперь я буду тебя предупреждать, когда батарея упадёт ниже 15% (если телефон не на зарядке).\nИспользуй /notify чтобы отключить.")
        else:
            await update.message.reply_text("🔕 Уведомления о разряде батареи **ОТКЛЮЧЕНЫ**!\n\nЯ больше не буду тебя предупреждать о разряде.\nИспользуй /notify чтобы включить обратно.")
    except Exception as e:
        logger.error(f"Ошибка в /notify: {e}")

async def click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if is_ignored_user(user):
            return
        user_data = get_user_data(user.id)
        if user_data and user_data.get('banned', 0) == 1:
            await update.message.reply_text("Ты забанен, лох! 🔨")
            return
        if not user_data:
            save_user_data(user.id, 0, [], "Без титула", user.username or "", user.first_name or "")
            user_data = get_user_data(user.id)
        clicks = user_data['clicks'] + 1
        achievements = user_data['achievements']
        new_achievements = []
        for threshold, name in ACHIEVEMENTS.items():
            if clicks == threshold and name not in achievements:
                new_achievements.append(name)
        if new_achievements:
            achievements.extend(new_achievements)
            await update.message.reply_text(f"🎉 Ачивка: {', '.join(new_achievements)}!\n{random.choice(INSULTS_ACHIEVE)}")
        save_user_data(user.id, clicks, achievements, user_data['title'],
                      user_data['username'], user_data['first_name'],
                      user_data['status'], user_data['banned'], user_data['notify_enabled'])
        response = f"👆 {clicks} кликов. {random.choice(INSULTS_CLICK)}"
        if user_data['title'] != "Без титула":
            response += f"\n👑 Титул: {user_data['title']}"
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Ошибка в /click: {e}")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if is_ignored_user(user):
            return
        user_data = get_user_data(user.id)
        if not user_data:
            await update.message.reply_text("Начни с /click, лох!")
            return
        if user_data.get('banned', 0) == 1:
            await update.message.reply_text("Ты забанен! 🔨")
            return
        is_dev = " 👑 РАЗРАБ" if is_admin(user.id) else ""
        notify_status = "Включены ✅" if user_data.get('notify_enabled', 1) == 1 else "Отключены 🔕"
        text = (
            f"📊 ПРОФИЛЬ\n\n"
            f"👤 Имя: {user.first_name or 'Без имени'}{is_dev}\n"
            f"🆔 ID: {user.id}\n"
            f"👑 Титул: {user_data['title']}\n"
            f"👆 Кликов: {user_data['clicks']}\n"
            f"🏆 Ачивок: {len(user_data['achievements'])}\n"
            f"💩 Статус: {user_data.get('status', 'Живой')}\n"
            f"🔔 Уведомления: {notify_status}\n"
        )
        if user_data['achievements']:
            text += "\n🎖️ Ачивки:\n" + "\n".join(f"• {a}" for a in user_data['achievements'][:10])
            if len(user_data['achievements']) > 10:
                text += f"\n...и ещё {len(user_data['achievements'])-10}"
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Ошибка в /profile: {e}")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if is_ignored_user(user):
            return
        conn = sqlite3.connect('clicks.db')
        cur = conn.cursor()
        cur.execute('SELECT user_id, clicks, title, username, first_name FROM users WHERE banned = 0 ORDER BY clicks DESC LIMIT 10')
        rows = cur.fetchall()
        conn.close()
        if not rows:
            await update.message.reply_text("Пока никто не кликал! 😡")
            return
        text = "🏆 ТОП 10\n\n"
        for i, (user_id, clicks, title, username, first_name) in enumerate(rows, 1):
            try:
                try:
                    chat = await context.bot.get_chat(user_id)
                    name = chat.username or chat.first_name or str(user_id)
                except:
                    name = username or first_name or str(user_id)
                title_display = f" [{title}]" if title != "Без титула" else ""
                text += f"{i}. {name}{title_display} — {clicks}\n"
            except:
                text += f"{i}. ID:{user_id} — {clicks}\n"
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Ошибка в /top: {e}")

async def redmi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if is_ignored_user(user):
            return
        user_data = get_user_data(user.id)
        if user_data and user_data.get('banned', 0) == 1:
            await update.message.reply_text("Ты забанен! 🔨")
            return

        now = time.time()
        last_call = _last_redmi_time.get(user.id, 0)
        if now - last_call < REDMI_COOLDOWN:
            remain = int(REDMI_COOLDOWN - (now - last_call)) + 1
            await update.message.reply_text(f"⏳ Подожди ещё {remain} секунд перед следующим /redmi!")
            return
        _last_redmi_time[user.id] = now

        start_time = time.time()
        info = await get_system_info_async()
        uptime = get_uptime()
        battery_icon = "🪫" if info['battery_percent'] < 20 else "🔋"
        if info['battery_is_charging']:
            battery_icon = "⚡"
        status_text = info['battery_status']
        ping_ms = round((time.time() - start_time) * 1000, 0)
        text = (
            f"📱 ХОСТ: REDMI GO\n"
            f"🤖 ОС: Android 11\n"
            f"⚙️ Процессор: Snapdragon 425\n"
            f"💾 Память: 8 ГБ (встроенная), 1 ГБ ОЗУ\n"
            f"📊 ЗАГРУЗКА CPU: {info['cpu_usage']}%\n"
            f"⚡ Частота CPU: {int(info['cpu_freq'])} МГц\n"
            f"💾 ОЗУ: {int(info['ram_used_mb'])}/{int(info['ram_total_mb'])} МБ ({info['ram_percent']}% занято, {int(info['ram_free_mb'])} МБ свободно)\n"
            f"🌡️ Температура CPU: {info['cpu_temp']}°C\n"
            f"{battery_icon} Батарея: {info['battery_percent']}%\n"
            f"🔌 {status_text}\n"
            f"🌡️ Температура батареи: {info['battery_temp']}°C\n"
            f"📶 Пинг: {ping_ms} мс\n"
            f"⏱️ Аптайм: {uptime}\n"
            f"{random.choice(RANDOM_REDMI_MESSAGES)}"
        )
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Ошибка в /redmi: {e}")
        await update.message.reply_text("Ошибка получения данных, попробуй позже.")

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if user.id != 5257003639:
            await update.message.reply_text("Ты не @tixconoff! Иди нахуй! 🖕")
            return
        await update.message.reply_text("📦 Создаю бэкап...")
        files_sent = 0
        if os.path.exists('clicks.db'):
            try:
                with open('clicks.db', 'rb') as f:
                    await context.bot.send_document(chat_id=user.id, document=f, filename='clicks.db')
                files_sent += 1
            except Exception as e:
                await update.message.reply_text(f"❌ Ошибка отправки clicks.db: {e}")
        else:
            await update.message.reply_text("❌ Файл clicks.db не найден.")
        if os.path.exists(BROADCAST_FILE):
            try:
                with open(BROADCAST_FILE, 'rb') as f:
                    await context.bot.send_document(chat_id=user.id, document=f, filename=BROADCAST_FILE)
                files_sent += 1
            except Exception as e:
                await update.message.reply_text(f"❌ Ошибка отправки {BROADCAST_FILE}: {e}")
        else:
            await update.message.reply_text(f"❌ Файл {BROADCAST_FILE} не найден.")
        if files_sent > 0:
            await update.message.reply_text("✅ Бэкап отправлен!")
    except Exception as e:
        logger.error(f"Ошибка /backup: {e}")
        await update.message.reply_text(f"Ошибка: {e}")

# ------------------- АДМИН-КОМАНДЫ -------------------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            await update.message.reply_text("Ты кто такой? Иди нахуй! 🚫")
            return
        keyboard = []
        for name, callback in ADMIN_FUNCTIONS.items():
            keyboard.append([InlineKeyboardButton(name, callback_data=f"admin_{callback}")])
        keyboard.append([InlineKeyboardButton("❌ Закрыть", callback_data="admin_close")])
        await update.message.reply_text("👑 АДМИН-ПАНЕЛЬ 👑", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Ошибка в /admin: {e}")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user = query.from_user
        if not is_admin(user.id):
            await query.edit_message_text("Ты кто такой? 🚫")
            return
        data = query.data.replace("admin_", "")
        if data == "close":
            await query.edit_message_text("Админка закрыта 👋")
        elif data == "broadcast":
            await query.edit_message_text("Используй /broadcast [текст]")
        elif data == "give_title":
            await query.edit_message_text("Используй /givetitle [ID] [титул]")
        elif data == "give_achievement":
            await query.edit_message_text("Используй /giveach [ID] [название]")
        elif data == "ban":
            await query.edit_message_text("Используй /ban [ID]")
        elif data == "unban":
            await query.edit_message_text("Используй /unban [ID]")
        elif data == "status":
            await query.edit_message_text("Используй /setstatus [ID] [статус]")
        elif data == "change_nick":
            await query.edit_message_text("Используй /setnick [ID] [ник]")
        elif data == "players":
            await query.edit_message_text("Используй /players")
        elif data == "stats":
            conn = sqlite3.connect('clicks.db')
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM users')
            total = cur.fetchone()[0]
            cur.execute('SELECT SUM(clicks) FROM users')
            clicks = cur.fetchone()[0] or 0
            conn.close()
            await query.edit_message_text(f"📊 СТАТИСТИКА\n\n👥 Всего: {total}\n👆 Кликов: {clicks}\n💻 Хост: Redmi Go")
        elif data == "addadmin":
            await query.edit_message_text("Используй /addadmin [ID]")
    except Exception as e:
        logger.error(f"Ошибка в admin_callback: {e}")

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            await update.message.reply_text("Ты кто такой? Это админ-команда! 🚫")
            return
        text = (
            "👑 АДМИН-HELP\n\n"
            "/admin – панель\n"
            "/players – все игроки\n"
            "/broadcast [текст] – рассылка\n"
            "/givetitle [ID] [титул] – выдать титул\n"
            "/giveach [ID] [название] – выдать ачивку\n"
            "/ban [ID] – забанить навсегда\n"
            "/unban [ID] – разбанить\n"
            "/setstatus [ID] [статус] – сменить статус\n"
            "/setnick [ID] [ник] – сменить ник\n"
            "/addadmin [ID] – добавить админа\n"
            "/stats – статистика\n"
        )
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Ошибка в /admhelp: {e}")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            return
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("/ban [ID]")
            return
        user_id = int(args[0])
        user_data = get_user_data(user_id)
        if not user_data:
            await update.message.reply_text("Пользователь не найден!")
            return
        if user_data['banned'] == 1:
            await update.message.reply_text("Уже забанен!")
            return
        save_user_data(user_id, user_data['clicks'], user_data['achievements'], user_data['title'],
                      user_data['username'], user_data['first_name'], user_data['status'], 1, user_data['notify_enabled'])
        await update.message.reply_text(f"🔨 Пользователь {user_id} забанен навсегда!")
        try:
            await context.bot.send_message(chat_id=user_id, text="🔨 Ты забанен навсегда, лох!")
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            return
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("/unban [ID]")
            return
        user_id = int(args[0])
        user_data = get_user_data(user_id)
        if not user_data:
            await update.message.reply_text("Пользователь не найден!")
            return
        if user_data['banned'] == 0:
            await update.message.reply_text("Он и так не забанен!")
            return
        save_user_data(user_id, user_data['clicks'], user_data['achievements'], user_data['title'],
                      user_data['username'], user_data['first_name'], user_data['status'], 0, user_data['notify_enabled'])
        await update.message.reply_text(f"🔓 Пользователь {user_id} разбанен!")
        try:
            await context.bot.send_message(chat_id=user_id, text="🔓 Тебя разбанили, лох! Радуйся!")
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            await update.message.reply_text("Ты кто такой? 🚫")
            return
        page = 0
        if context.args and context.args[0].isdigit():
            page = int(context.args[0]) - 1
        conn = sqlite3.connect('clicks.db')
        cur = conn.cursor()
        cur.execute('SELECT user_id, clicks, title, username, first_name, status, banned FROM users ORDER BY clicks DESC')
        rows = cur.fetchall()
        conn.close()
        if not rows:
            await update.message.reply_text("Нет игроков!")
            return
        per_page = 20
        total_pages = (len(rows) + per_page - 1) // per_page
        if page >= total_pages:
            page = total_pages - 1
        start = page * per_page
        end = min(start + per_page, len(rows))
        text = f"👥 ИГРОКИ ({page+1}/{total_pages})\n\n"
        for i, (uid, clicks, title, uname, fname, status, banned) in enumerate(rows[start:end], start+1):
            name = uname or fname or str(uid)
            if len(name) > 12:
                name = name[:10] + ".."
            title_disp = title if title != "Без титула" else "Нет"
            ban = "🚫" if banned else ""
            text += f"{i}. {name} {ban} | {clicks} | {title_disp} | {status}\n"
        keyboard = []
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"players_{page-1}"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"players_{page+1}"))
        if nav:
            keyboard.append(nav)
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
    except Exception as e:
        logger.error(f"Ошибка /players: {e}")

async def players_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user = query.from_user
        if not is_admin(user.id):
            await query.edit_message_text("Ты кто?")
            return
        page = int(query.data.replace("players_", ""))
        conn = sqlite3.connect('clicks.db')
        cur = conn.cursor()
        cur.execute('SELECT user_id, clicks, title, username, first_name, status, banned FROM users ORDER BY clicks DESC')
        rows = cur.fetchall()
        conn.close()
        if not rows:
            await query.edit_message_text("Нет игроков!")
            return
        per_page = 20
        total_pages = (len(rows) + per_page - 1) // per_page
        if page >= total_pages:
            page = total_pages - 1
        if page < 0:
            page = 0
        start = page * per_page
        end = min(start + per_page, len(rows))
        text = f"👥 ИГРОКИ ({page+1}/{total_pages})\n\n"
        for i, (uid, clicks, title, uname, fname, status, banned) in enumerate(rows[start:end], start+1):
            name = uname or fname or str(uid)
            if len(name) > 12:
                name = name[:10] + ".."
            title_disp = title if title != "Без титула" else "Нет"
            ban = "🚫" if banned else ""
            text += f"{i}. {name} {ban} | {clicks} | {title_disp} | {status}\n"
        keyboard = []
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"players_{page-1}"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"players_{page+1}"))
        if nav:
            keyboard.append(nav)
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
    except Exception as e:
        logger.error(f"Ошибка players_pagination: {e}")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            return
        text = update.message.text.replace("/broadcast ", "")
        if not text:
            await update.message.reply_text("/broadcast [текст]")
            return
        msg = await update.message.reply_text("📢 Рассылка...")
        conn = sqlite3.connect('clicks.db')
        cur = conn.cursor()
        cur.execute('SELECT user_id FROM users')
        users = cur.fetchall()
        conn.close()
        sent = 0
        for (uid,) in users:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 СООБЩЕНИЕ ОТ АДМИНА 📢\n\n{text}")
                sent += 1
                await asyncio.sleep(0.2)
            except:
                pass
        await msg.edit_text(f"✅ Отправлено {sent} пользователям")
    except Exception as e:
        logger.error(f"Ошибка broadcast: {e}")

async def give_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            return
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("/givetitle [ID] [титул]")
            return
        uid = int(args[0])
        title = " ".join(args[1:])
        data = get_user_data(uid)
        if not data:
            await update.message.reply_text("Пользователь не найден!")
            return
        save_user_data(uid, data['clicks'], data['achievements'], title,
                      data['username'], data['first_name'], data['status'], data['banned'], data['notify_enabled'])
        await update.message.reply_text(f"✅ Титул '{title}' выдан {uid}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def give_achievement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            return
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("/giveach [ID] [название]")
            return
        uid = int(args[0])
        ach = " ".join(args[1:])
        data = get_user_data(uid)
        if not data:
            await update.message.reply_text("Пользователь не найден!")
            return
        if ach not in data['achievements']:
            data['achievements'].append(ach)
            save_user_data(uid, data['clicks'], data['achievements'], data['title'],
                          data['username'], data['first_name'], data['status'], data['banned'], data['notify_enabled'])
            await update.message.reply_text(f"✅ Ачивка '{ach}' выдана {uid}")
        else:
            await update.message.reply_text("У него уже есть эта ачивка!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            return
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("/setstatus [ID] [статус]")
            return
        uid = int(args[0])
        status = " ".join(args[1:])
        data = get_user_data(uid)
        if not data:
            await update.message.reply_text("Пользователь не найден!")
            return
        save_user_data(uid, data['clicks'], data['achievements'], data['title'],
                      data['username'], data['first_name'], status, data['banned'], data['notify_enabled'])
        await update.message.reply_text(f"✅ Статус {uid} изменён на '{status}'")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def set_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            return
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("/setnick [ID] [ник]")
            return
        uid = int(args[0])
        nick = " ".join(args[1:])
        data = get_user_data(uid)
        if not data:
            await update.message.reply_text("Пользователь не найден!")
            return
        save_user_data(uid, data['clicks'], data['achievements'], data['title'],
                      nick, data['first_name'], data['status'], data['banned'], data['notify_enabled'])
        await update.message.reply_text(f"✅ Ник {uid} изменён на '{nick}'")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            return
        conn = sqlite3.connect('clicks.db')
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM users')
        total = cur.fetchone()[0]
        cur.execute('SELECT SUM(clicks) FROM users')
        clicks = cur.fetchone()[0] or 0
        conn.close()
        await update.message.reply_text(f"📊 СТАТИСТИКА\n\n👥 Всего: {total}\n👆 Кликов: {clicks}\n💻 Хост: Redmi Go\n💩 Статус: {random.choice(['Работает', 'Тормозит', 'Греется'])}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_admin(user.id):
            await update.message.reply_text("Ты не админ!")
            return
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("/addadmin [ID]")
            return
        new_id = int(args[0])
        if new_id in ADMIN_IDS:
            await update.message.reply_text("Уже админ!")
            return
        ADMIN_IDS.append(new_id)
        await update.message.reply_text(f"✅ Пользователь {new_id} добавлен в админы!")
        try:
            await context.bot.send_message(chat_id=new_id, text="👑 Ты теперь админ! Используй /admin")
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# ------------------- МАГАЗИН -------------------
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if is_ignored_user(user):
            return
        if update.message.chat.type != "private":
            await update.message.reply_text("⚠️ Магазин ТОЛЬКО в ЛС!")
            return
        data = get_user_data(user.id)
        if not data:
            await update.message.reply_text("Начни с /click, лох!")
            return
        if data.get('banned', 0) == 1:
            await update.message.reply_text("Ты забанен! 🔨")
            return
        text = f"🛒 МАГАЗИН 🛒\n\n💰 Кликов: {data['clicks']}\n\nВыбери категорию:"
        keyboard = [
            [InlineKeyboardButton("👑 Титулы", callback_data="shop_titles")],
            [InlineKeyboardButton("📤 Отправить гифку всем (250 кликов)", callback_data="shop_gif")]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Ошибка /shop: {e}")

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user = query.from_user
        data = get_user_data(user.id)
        if not data:
            await query.edit_message_text("Начни с /click!")
            return
        if data.get('banned', 0) == 1:
            await query.edit_message_text("Ты забанен! 🔨")
            return
        if query.data == "shop_titles":
            await show_shop_page(query, user, 0)
        elif query.data == "shop_gif":
            if data['clicks'] < GIF_PRICE:
                await query.edit_message_text(f"❌ У тебя {data['clicks']} кликов, нужно {GIF_PRICE}!")
                return
            _awaiting_gif[user.id] = {'step': 'waiting_gif'}
            await query.edit_message_text(
                f"📤 Отправка гифки всем (стоимость: {GIF_PRICE} кликов)\n\n"
                "⚠️ **ПРЕДУПРЕЖДЕНИЕ О 18+!**\n"
                "Запрещено отправлять порнографию, насилие и другой запрещённый контент.\n"
                "**За нарушение — бан навсегда!**\n\n"
                "Отправь гифку (анимацию) в этот чат:"
            )
        elif query.data.startswith("buy_"):
            title = query.data.replace("buy_", "")
            if title not in SHOP_TITLES:
                await query.edit_message_text("❌ Такого титула нет!")
                return
            price = SHOP_TITLES[title]
            if data['clicks'] < price:
                await query.edit_message_text(f"❌ Нужно {price} кликов! У тебя {data['clicks']}")
                return
            if title == data['title']:
                await query.edit_message_text("❌ У тебя уже есть этот титул!")
                return
            new_clicks = data['clicks'] - price
            save_user_data(user.id, new_clicks, data['achievements'], title,
                          data['username'], data['first_name'], data['status'], data['banned'], data['notify_enabled'])
            await query.edit_message_text(f"✅ Купил '{title}' за {price} кликов!\n💰 Осталось: {new_clicks}")
        elif query.data.startswith("shop_page_"):
            page = int(query.data.replace("shop_page_", ""))
            await show_shop_page(query, user, page)
    except Exception as e:
        logger.error(f"Ошибка shop_callback: {e}")

async def show_shop_page(query, user, page):
    try:
        data = get_user_data(user.id)
        if not data:
            await query.edit_message_text("Начни с /click!")
            return
        titles = list(SHOP_TITLES.items())
        total_pages = (len(titles) + SHOP_PAGE_SIZE - 1) // SHOP_PAGE_SIZE
        if page >= total_pages:
            page = total_pages - 1
        if page < 0:
            page = 0
        start = page * SHOP_PAGE_SIZE
        end = min(start + SHOP_PAGE_SIZE, len(titles))
        text = f"👑 ТИТУЛЫ (стр. {page+1}/{total_pages})\n\n💰 Кликов: {data['clicks']}\n👑 Текущий: {data['title']}\n\n"
        keyboard = []
        for title, price in titles[start:end]:
            if title == data['title']:
                keyboard.append([InlineKeyboardButton(f"✅ {title} (активен)", callback_data=f"shop_{title}")])
            elif data['clicks'] >= price:
                keyboard.append([InlineKeyboardButton(f"🛒 {title} ({price})", callback_data=f"buy_{title}")])
            else:
                keyboard.append([InlineKeyboardButton(f"🔒 {title} ({price})", callback_data=f"shop_{title}")])
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"shop_page_{page-1}"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"shop_page_{page+1}"))
        if nav:
            keyboard.append(nav)
        keyboard.append([InlineKeyboardButton("🔙 Назад в магазин", callback_data="shop_back")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Ошибка show_shop_page: {e}")

async def shop_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user = query.from_user
        data = get_user_data(user.id)
        if not data:
            await query.edit_message_text("Начни с /click!")
            return
        text = f"🛒 МАГАЗИН 🛒\n\n💰 Кликов: {data['clicks']}\n\nВыбери категорию:"
        keyboard = [
            [InlineKeyboardButton("👑 Титулы", callback_data="shop_titles")],
            [InlineKeyboardButton("📤 Отправить гифку всем (250 кликов)", callback_data="shop_gif")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Ошибка shop_back: {e}")

# ------------------- ОБРАБОТЧИК ГИФКИ -------------------
async def handle_gif_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in _awaiting_gif:
        return
    state = _awaiting_gif[user.id]
    try:
        if state['step'] == 'waiting_gif':
            if update.message.animation:
                _awaiting_gif[user.id]['file_id'] = update.message.animation.file_id
                _awaiting_gif[user.id]['step'] = 'waiting_text'
                await update.message.reply_text("✅ Гифка получена!\n\nТеперь напиши текст для подписи:")
            else:
                await update.message.reply_text("❌ Это не гифка! Отправь анимацию (GIF).")
        elif state['step'] == 'waiting_text':
            text = update.message.text
            if not text:
                await update.message.reply_text("❌ Напиши текст!")
                return
            _awaiting_gif[user.id]['text'] = text
            _awaiting_gif[user.id]['step'] = 'confirm'
            keyboard = [
                [InlineKeyboardButton("✅ Да, отправить всем", callback_data="gif_confirm"),
                 [InlineKeyboardButton("❌ Отмена", callback_data="gif_cancel")]]
            ]
            await update.message.reply_text(f"📝 Текст: {text}\n\nПодтверждаешь отправку гифки с этим текстом всем пользователям?\nКлики будут списаны.", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Ошибка handle_gif_input: {e}")

async def gif_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user = query.from_user
        if user.id not in _awaiting_gif:
            await query.edit_message_text("❌ Процесс не найден.")
            return
        state = _awaiting_gif[user.id]
        if query.data == "gif_cancel":
            del _awaiting_gif[user.id]
            await query.edit_message_text("❌ Отправка отменена.")
            return
        if query.data == "gif_confirm":
            data = get_user_data(user.id)
            if not data:
                await query.edit_message_text("Ошибка данных.")
                return
            if data['clicks'] < GIF_PRICE:
                await query.edit_message_text(f"❌ У тебя {data['clicks']} кликов, нужно {GIF_PRICE}!")
                return
            new_clicks = data['clicks'] - GIF_PRICE
            save_user_data(user.id, new_clicks, data['achievements'], data['title'],
                          data['username'], data['first_name'], data['status'], data['banned'], data['notify_enabled'])
            conn = sqlite3.connect('clicks.db')
            cur = conn.cursor()
            cur.execute('SELECT user_id FROM users WHERE banned = 0')
            users = cur.fetchall()
            conn.close()
            sent = 0
            file_id = state['file_id']
            user_text = state['text']
            caption = f"Анонимный игрок за 250 кликов скинул это!\n\n{user_text}"
            admin_log = f"📤 Отправлена гифка пользователем ID {user.id} (@{user.username or 'без юзернейма'})\nТекст: {user_text}"
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(chat_id=admin_id, text=admin_log)
                except:
                    pass
            for (uid,) in users:
                try:
                    await context.bot.send_animation(chat_id=uid, animation=file_id, caption=caption)
                    sent += 1
                    await asyncio.sleep(0.3)
                except:
                    pass
            del _awaiting_gif[user.id]
            await query.edit_message_text(f"✅ Гифка отправлена {sent} пользователям!\n💰 Осталось кликов: {new_clicks}")
    except Exception as e:
        logger.error(f"Ошибка gif_confirm_callback: {e}")

# ------------------- ФОНОВЫЕ ЗАДАЧИ -------------------
async def battery_monitor(application: Application):
    global _last_battery_warning_time
    while not _stop_event.is_set():
        try:
            level, status, is_charging, temp = get_battery_info()
            if is_charging or level >= 15:
                await asyncio.sleep(60)
                continue
            now = time.time()
            conn = sqlite3.connect('clicks.db')
            cur = conn.cursor()
            cur.execute('SELECT user_id, notify_enabled FROM users WHERE banned = 0')
            users = cur.fetchall()
            conn.close()
            for uid, enabled in users:
                if enabled == 0:
                    continue
                if now - _last_battery_warning_time.get(uid, 0) < 300:
                    continue
                msg = random.choice(BATTERY_WARNING_MESSAGES).format(level=level, status=status, temp=temp)
                try:
                    await application.bot.send_message(chat_id=uid, text=msg)
                    _last_battery_warning_time[uid] = now
                    await asyncio.sleep(0.3)
                except:
                    pass
        except Exception as e:
            logger.error(f"battery_monitor error: {e}")
        await asyncio.sleep(60)

async def send_startup_notification(application: Application):
    try:
        conn = sqlite3.connect('clicks.db')
        cur = conn.cursor()
        cur.execute('SELECT user_id FROM users')
        users = cur.fetchall()
        conn.close()
        if not users:
            return
        text = (
            f"🚀 БОТ ПЕРЕЗАПУЩЕН, ДОЛБОЁБЫ! 🚀\n\n"
            f"Версия: {BOT_VERSION}\n"
            "Хост: Redmi Go (Android 11, 8 ГБ памяти, 1 ГБ ОЗУ)\n"
            "Всё работает, можете продолжать кликать!\n\n"
            "📌 Команды:\n"
            "/click - кликнуть\n"
            "/profile - профиль\n"
            "/top - топ-10\n"
            "/shop - магазин (ТОЛЬКО В ЛИЧКЕ!)\n"
            "/redmi - информация о хосте\n"
            "/notify - уведомления о разряде\n"
            "/changelog - список изменений\n\n"
            "P.S. Если что-то сломалось — идите нахуй, я не отвечаю! 🖕"
        )
        for (uid,) in users:
            try:
                await application.bot.send_message(chat_id=uid, text=text)
                await asyncio.sleep(0.2)
            except:
                pass
    except Exception as e:
        logger.error(f"startup notification error: {e}")

# ------------------- MAIN -------------------
def main():
    init_db()
    try:
        app = Application.builder().token(TOKEN).build()
    except Exception as e:
        logger.error(f"Ошибка создания приложения: {e}")
        return

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("click", click))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("redmi", redmi))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("notify", notify_command))
    app.add_handler(CommandHandler("changelog", changelog))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("admhelp", admin_help))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("players", players_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("givetitle", give_title))
    app.add_handler(CommandHandler("giveach", give_achievement))
    app.add_handler(CommandHandler("setstatus", set_status))
    app.add_handler(CommandHandler("setnick", set_nick))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("backup", backup_command))
    app.add_handler(CommandHandler("unknown", lambda u,c: u.message.reply_text("Неизвестная команда! /start")))

    # Callbacks
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern="^(shop_|buy_|shop_page_)"))
    app.add_handler(CallbackQueryHandler(shop_back, pattern="^shop_back$"))
    app.add_handler(CallbackQueryHandler(gif_confirm_callback, pattern="^(gif_confirm|gif_cancel)$"))
    app.add_handler(CallbackQueryHandler(players_pagination, pattern="^players_"))

    # Обработчики сообщений
    app.add_handler(MessageHandler(filters.ANIMATION | filters.TEXT & ~filters.COMMAND, handle_gif_input))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, lambda u,c: None))
    app.add_handler(MessageHandler(filters.ALL, lambda u,c: None), group=0)

    logger.info("🚀 Бот запущен!")
    logger.info(f"👑 Админы: {ADMIN_IDS}")
    logger.info(f"🔋 Мониторинг батареи активен")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(send_startup_notification(app))
    loop.create_task(battery_monitor(app))
    loop.create_task(clean_redmi_history())

    try:
        app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
