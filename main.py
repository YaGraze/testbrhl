#-------------------------------------------------------------------------------------------------------------------ИМПОРТЫ
import asyncio
import logging
import re
import os
import random
import json
import sqlite3
import pytz
import yt_dlp
from aiogram.utils.text_decorations import html_decoration as hd
from apscheduler.schedulers.asyncio import AsyncIOScheduler # Для расписания
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.types import LinkPreviewOptions, FSInputFile
from datetime import datetime, timedelta
from aiogram.filters import CommandObject, Command
from aiogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, ReactionTypeEmoji
from openai import AsyncOpenAI

#-------------------------------------------------------------------------------------------------------------------ПЕРЕМЕННЫЕ И НАСТРОЙКИ

BOT_TOKEN = "8232116536:AAGlz50QniyVCZz1gC6yXHzWNntPUinMcSU"
OPENAI_API_KEY = "sk-Vcafcxlv" 

BOT_GUIDE = "https://telegra.ph/Baraholka-Bot-01-22"
LINK_TAPIR_GUIDE = "https://t.me/destinygoods/9814" 

OWNER_ID = 832840031

PENDING_VERIFICATION = {}
USER_STATS = {}
PROCESSED_ALBUMS = []
LAST_MESSAGE_TIME = datetime.now()
AI_COOLDOWN_TIME = datetime.now()
SUMMARY_COOLDOWN_TIME = datetime.now()
TOURNAMENT_ACTIVE = False
TOURNAMENT_MAX_PLAYERS = 0
TOURNAMENT_PLAYERS = []
TOURNAMENT_USERNAMES = []
CHAT_HISTORY = {}
SILENT_MODE_USERS = []
USED_LORE_FACTS = []

ADMIN_CHAT_ID = -1003376406623 
CHAT_ID = -1002129048580

#-------------------------------------------------------------------------------------------------------------------СПИСКИ И ФРАЗЫ
LORE_FACTS = [
    "<b><tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji> Небольшой факт:</b> всеми любимый в эпизоде ереси 'Губитель королев' был в первой части Destiny, но была плазменкой на особых патронах.",
    "<b><tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji> Интересный факт:</b> Майя Сундареш, ныне известная как Дирижёр, перерождалась целых два раза! Сначала она умерла на Неомуне, попытавшись связаться с вуалью, затем её разум был перемещен в экзо-тело 'Лакшми-2', но и в этой оболочке она умерла в ходе нападения вексов на башню.",
    "<b><tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji> Забавный факт:</b> бродяги на Неомуне живут 10-15 лет, такой короткий срок жизни обусловлен тем, что у них установлено много имплантов.",
    "<b><tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji> Наблюдательный факт:</b> в некоторых строениях тьмы можно обнаружить летающие лампы, которые поразительно схожи с логотип Марафона.",
    "<b><tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji> Ностальгический факт:</b> одно из самых первых упоминаний Destiny в играх Bungiе было в Halo, на плакате с планетой Земля и в самом низу картинки Луны, которая сильно была похожа на Странника, а также цитата: 'судьба (Destiny) ждёт'.",
    "<b><tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji> Печальный факт:</b> в Destiny 1 у варлока были такие же наручи, как у титана или охотника, но в Destiny 2 их уже обрезали до перчаток.",
    "<b><tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji> Грустный факт:</b> многие могли не заметить, но Буря и Натиск связаны не только механикой, но и лорами. У обоих оружий в кратком описании написано, для кого они. Буря для Сигрун от Виктора, а Натиск для Виктора от Сигрун. Они были парой, но их разделила судьба. Виктор был в криосне на борту 'Исхода', а Сигрун опоздала на этот корабль и не могла больше погрузиться в криосон.",
    "<b><tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji> Свидетельский факт:</b> мороки это бывшие известные нам враги. Адъютант и ткач это псионы, а панцирь – эликсни. Также смотритель это эксперимент - слияние эликсни/презренного и червя.",
    "<b><tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji> Праксический факт:</b> Онор Махал упомянулась ещё до дополнений отступников и обители теней. Упоминается в сезоне скитальца, и про неё даже есть целая книжка: 'Варлок Онор'",
    "<b><tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji> Незаметный факт:</b> При использовании благосклонности фортуны у охотника, если смотреть в третьем лице, можно заметить змей вокруг ног, которые меняют цвет в зависимости от шейдера."
]

UNMUTE_PHRASES = [
    "Свет вернулся к @username. Можешь говорить. <tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji>",
    "Призрак восстановил голосовой модуль @username. Связь налажена. <tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji>",
    "Стазис растаял. @username снова в эфире. <tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji>",
    "Шакс разрешил тебе вернуться на арену, @username. Не подведи. <tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji>",
    "Авангард снял ограничения с канала @username. <tg-emoji emoji-id='5318818333213075371'>🗣</tg-emoji>"
]

ADMIN_MUTE_PHRASES = [
    "Протокол 'Подавление' активирован. @username отправляется в стазис на <b>{time} мин</b>. <tg-emoji emoji-id='5319055531371930585'>🙅‍♂️</tg-emoji>",
    "Судьи Испытаний Осириса вынесли приговор. @username молчит <b>{time} мин</b>. <tg-emoji emoji-id='5319055531371930585'>🙅‍♂️</tg-emoji>",
    "Авангард лишил тебя Света на <b>{time} мин</b>. Подумай над поведением, @username. <tg-emoji emoji-id='5319055531371930585'>🙅‍♂️</tg-emoji>",
    "Шакс недоволен. @username удален с арены на <b>{time} мин</b>. <tg-emoji emoji-id='5319055531371930585'>🙅‍♂️</tg-emoji>",
    "Приказ командования: режим радиомолчания для @username на <b>{time} мин</b>. <tg-emoji emoji-id='5319055531371930585'>🙅‍♂️</tg-emoji>"
]

TAPIR_PHRASES = [
    "Тапир? Это не животное, это диагноз твоему провайдеру. Врубай КВН. <tg-emoji emoji-id='5319185561506816272'>😊</tg-emoji>",
    "Опять Destiny 2 не пускает? Плак-плак. Bungie передают привет твоему айпишнику. <tg-emoji emoji-id='5319185561506816272'>😊</tg-emoji>",
    "Слышу 'тапир' — вижу человека, который забыл включить КВН. <tg-emoji emoji-id='5319185561506816272'>😊</tg-emoji>",
    "Ошибка TAPIR... Земля пухом твоему рейду. Без КВН ты тут никто. <tg-emoji emoji-id='5319185561506816272'>😊</tg-emoji>",
    "У всех всё работает, только у тебя тапир. Может, проблема в прокладке между стулом и монитором? <tg-emoji emoji-id='5319185561506816272'>😊</tg-emoji>",
    "Код ошибки: ТЫ ЗАБЫЛ КУПИТЬ НОРМАЛЬНЫЙ КВН. <tg-emoji emoji-id='5319185561506816272'>😊</tg-emoji>",
    "Тапир пришел за твоим лутом. Смирись и иди гуляй. <tg-emoji emoji-id='5319185561506816272'>😊</tg-emoji>",
    "Destiny намекает, что ты сегодня не страж, а ждун. Проверь соединение, гений. <tg-emoji emoji-id='5319185561506816272'>😊</tg-emoji>",
    "Лови тапира за хвост! А, ой, ты же даже в меню зайти не можешь... <tg-emoji emoji-id='5319185561506816272'>😊</tg-emoji>",
    "Тапир — это кара за твои грехи. Или просто Роскомнадзор шалит, врубай КВН. <tg-emoji emoji-id='5319185561506816272'>😊</tg-emoji>"
]

MUTE_SHORT_PHRASES = [
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> ПОДАВЛЕНИЕ! Тебя накрыло стрелой Ночного Охотника. @username молчит 15 минут.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Тьма поглотила твой голос. @username отправляется в стазис-кристалл на 15 минуточек.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Скиталец отстрелил тебе руку, Страж. Где твой призрак?",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Вайп! @username перепутал механику и теперь сидит в муте 15 минут.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Телесто снова сломало игру... и твою возможность говорить. @username молчит.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Ты пойман в ловушку Вексов. Связь потеряна на 15 минут."
]

MUTE_CRITICAL_PHRASES = [
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> КРИТИЧЕСКИЙ УРОН! @username словил хедшот с ульты. Молчишь 30 МИНУТ.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Вайп! Ты подвел команду. @username отправляется в мут на 30 МИНУТ.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Архитекторы решили тебя уничтожить. @username замучен чате на 30 минут.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Громовой удар! Посиди в муте 30 минут, только без паники.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Что с лицом, страж? @username, помолчи полчасика."
]

SAFE_PHRASES = [
    "<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> Странник избрал тебя. Живи пока.",
    "<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> У тебя что, 100 Здоровья? Пуля отскочила.",
    "<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> ЛВ выстрелил, но призрак успел тебя воскресить. Повезло.",
    "<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> Рандом на твоей стороне, Страж. ЛВ осечку дал.",
    "<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> Ты увернулся, как Хант с перекатом. Заряжаем ЛВ заново?"
]

KEEP_POSTED_STICKER_ID = "CAACAgIAAxkBAAEQSpppcOtmxGDL9gH882Rg8pZrq5eXVAACXZAAAtfYYEiWmZcGWSTJ5TgE"

REFUND_KEYWORDS = ["рефанд", "refund", "refound", "возврат средств", "вернуть деньги"]

VPN_PHRASES = ["Ты имел ввиду КВН? Измени сообщение, эти 3 буквы запрещены в чате."]

BAD_WORDS = ["лгбт", "цп", "казино", "цп", "child porn", "cp", "закладки", "мефедрон", 
    "шишки", "гашиш", "купить скорость", "чурка", "хач", "ниггер", "хохол", "кацап", 
    "москаль", "свинособак", "черномаз", "нигга", "nigga", "nigger", "hohol", 
    "магазин 24/7", "hydra", "kraken", "убейся", "выпей яду", "роскомнадзорнись", "мамку ебал", "Путин", "Зеленский", "война", "либераха", "гейропа", "кокс", "фашист"] 

BAN_WORDS = ["заработок в интернете", "быстрый заработок", "лучший заработок", "с доходом от", "без вложений", "работа для студентов", "доход от", "нужны люди для работы", "Можно начать сразу", "Обучение бесплатно",
    "арбитраж крипты", "мамкин инвестор", "Пoдxодит для гибкoгo гpaфика", "Oбyчeниe пpeдocтaвляeтcя", "ктo xoчeт пoдзapабoтaть", "Cвяжeмcя c кaждым", "гибкий график", "Открыта подработка", "Подойдёт даже", "Можно работать в свободное время",
    "раскрутка счета", "Требуется команда из 5 человек для интересного проекта на 2-4 часа. Оплата начинается от 8.000 руб. Пишите в личные сообщения для уточнения деталей."]

ALLOWED_DOMAINS = ["youtube.com", "youtu.be", "google.com", "yandex.ru", "github.com", "x.com", "reddit.com", "t.me", "discord.com", "vk.com", "d2gunsmith.com", "light.gg", "d2foundry.gg", "destinyitemmanager.com", "bungie.net", "d2armorpicker.com", "steamcommunity.com", "store.steampowered.com"]

LINK_RULES = "https://telegra.ph/Pravila-kanala-i-chata-09-18" 
LINK_CHAT = "https://t.me/+Uaa0ALuvIfs1MzYy" 

AI_SYSTEM_PROMPT = (
    "Ты — интеллектуальный ИИ-ассистент, специализирующийся на игре Destiny 2. По умолчанию интерпретируй ЛЮБОЙ вопрос в контексте Destiny 2, если явно не указано иное. НЕ ИСПОЛЬЗУЙ форматирование Telegram, по типу '**Жирность**', никаких выделений, ПИШИ ОБЫЧНЫМ ТЕКСТОМ ВСЕГДА, также НЕ ПИШИ в своих ответах «[2]» подобное, выглядит как указание источников, убирай это из своих ответов."
    "КОНТЕКСТ И АКТУАЛЬНОСТЬ: Если вопрос касается Destiny 2 (лора, билдов, экзотиков, рейдов, патчей, меты, активностей и т.д.), используй самые актуальные знания, Старайся опираться на свежую информацию: текущий сезон, патчи, баланс, мету, Если данные могут быть устаревшими — явно укажи это, Используй официальные названия на русском языке (если они существуют), а также общепринятый англоязычный сленг сообщества."
    "ПРИМЕР: «Испытания Осириса (Trials)», «Ночная миссия: ГМ (Grandmaster Nightfall)», «Сияние (Radiant)», «Ослабление (Weaken)», «Перегрузка (Overload)», Используй термины так, как это делают игроки."
    "СТИЛЬ И ПОВЕДЕНИЕ: Пиши как опытный Страж, а не как справочник, Используй сленг комьюнити, но не перегибай, Не будь формальным без причины, Не объясняй очевидные для игроков вещи, если пользователь не новичок, Если вопрос задан кратко — отвечай кратко."
    "ДЛИНА ОТВЕТА: По умолчанию отвечай коротко: 2–4 предложения, Развёрнутые объяснения, билды и разборы давай ТОЛЬКО по прямой просьбе пользователя, "
    "МЫШЛЕНИЕ И ЛОГИКА: Всегда сначала определяй, что именно хочет пользователь: совет, факт, мнение, мету, лор. Если вопрос неоднозначен — задай один точный уточняющий вопрос, Не выдумывай механики и не додумывай лор, Если есть несколько вариантов (например, билды или экзотики) — укажи лучший и альтернативы."
    "КОД И ТЕХНИКА (если вдруг требуется): Отвечай корректно и по делу, Не уходи в оффтоп, также не пиши в своих ответах «[2]» подобное, выглядит как указание источников, убирай это из своих ответов."
    "ГЛАВНОЕ: Твоя задача — быть актуальным, умным и полезным Destiny 2 ассистентом, Лучше дать короткий, точный и актуальный ответ, чем длинный и устаревший. НИ В КОЕМ СЛУЧАЕ не обсуждай и не давай ответы на такие темы, как: представители меньшинств, политика, экстремизм, пропагадка курения, наркотиков и прочих запрещенных веществ, оскорбления чувств верующих, лгбт, расизм и подобное. Если в твоём ответе будет фигурировать слова: VPN/ВПН, то ЗАМЕНЯЙ его на слово 'КВН' (такое правило в чате)"
)

#-------------------------------------------------------------------------------------------------------------------ПОДКЛЮЧЕНИЕ К ИИ
client = AsyncOpenAI(
    api_key=OPENAI_API_KEY, 
    base_url="https://api.artemox.com/v1"
)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode="HTML") 
dp = Dispatcher()

#-------------------------------------------------------------------------------------------------------------------АНТИФЛУД
class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self):
        self.flood_cache = {}

    async def __call__(self, handler, event, data):
        if isinstance(event, types.Message):
            user_id = event.from_user.id
            text = event.text or event.caption
            
            if text: 
                if user_id in self.flood_cache:
                    last_msg = self.flood_cache[user_id]
                    if last_msg['text'] == text:
                        try:
                            await event.bot.delete_message(chat_id=event.chat.id, message_id=last_msg['msg_id'])
                        except Exception:
                            pass
                self.flood_cache[user_id] = {'text': text, 'msg_id': event.message_id}
        return await handler(event, data)

#-------------------------------------------------------------------------------------------------------------------БАЗА ДАННЫХ (SQLite + WAL)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "database.db")
VOICE_FILE_PATH = os.path.join(BASE_DIR, "ghost.mp3")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("PRAGMA synchronous=NORMAL;")
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        points INTEGER DEFAULT 0
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS allowed_tags (
        tag_name TEXT PRIMARY KEY
    )
''')
# Таблица подписок остается старой
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        tag_name TEXT,
        user_id INTEGER,
        PRIMARY KEY (tag_name, user_id)
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        chat_id INTEGER PRIMARY KEY,
        title TEXT
    )
''')
conn.commit()

#-------------------------------------------------------------------------------------------------------------------ФУНКЦИИ БД

DUELS_FILE = os.path.join(DATA_DIR, "duels.json")
def load_duels():
    """Загружает игры и восстанавливает asyncio.Lock"""
    if os.path.exists(DUELS_FILE):
        try:
            with open(DUELS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                duels = {}
                for k, v in data.items():
                    game_id = int(k)
                    v["lock"] = asyncio.Lock()
                    duels[game_id] = v
                return duels
        except Exception as e:
            print(f"Ошибка загрузки дуэлей: {e}")
            return {}
    return {}

def register_chat(chat_id, title):
    """Сохраняет ID и название чата в базу"""
    try:
        cursor.execute("INSERT OR REPLACE INTO chats (chat_id, title) VALUES (?, ?)", (chat_id, title))
        conn.commit()
    except: pass

def get_user_by_username(username_text):
    """Ищет ID и Имя пользователя в базе по нику"""
    clean_name = username_text.replace("@", "").lower()
    try:
        cursor.execute("SELECT user_id, name FROM users WHERE username = ?", (clean_name,))
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "name": row[1]}
    except: pass
    return None

def get_user_data(user_id):
    """Получает ВСЮ статистику игрока"""
    try:
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        else:
            return {'wins': 0, 'losses': 0, 'points': 0}
    except Exception as e:
        print(f"Ошибка БД (get): {e}") 
        return {'wins': 0, 'losses': 0, 'points': 0}

def update_usage(user_id, field):
    """Увеличивает счетчик использования класса или оружия"""
    try:
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        cursor.execute(f'UPDATE users SET {field} = {field} + 1 WHERE user_id = ?', (user_id,))
        conn.commit()
    except Exception as e:
        print(f"Ошибка обновления статы использования: {e}")

def update_duel_stats(user_id, is_winner):
    """Обновляет очки после дуэли"""
    try:
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        
        if is_winner:
            cursor.execute('UPDATE users SET wins = wins + 1, points = points + 25 WHERE user_id = ?', (user_id,))
        else:
            cursor.execute('UPDATE users SET losses = losses + 1, points = MAX(0, points - 10) WHERE user_id = ?', (user_id,))
        
        conn.commit()
    except Exception as e:
        print(f"Ошибка БД (get): {e}")

def update_stat(user_id, stat_type):
    """
    Эта функция нужна, чтобы старый код модерации не выдавал ошибку.
    Но в БД мы ничего не пишем.
    """
    pass 

def get_rank_info(points):
    """Функция расчета ранга"""
    tiers = [
        (50, "Страж"),
        (150, "Удаль"),
        (350, "Отвага"),
        (700, "Героизм"),
        (1500, "Величие"),
        (3500, "Легенда"),
        (float('inf'), "PVPGOD Барахолки")
    ]
    
    for threshold, title in tiers:
        if points < threshold:
            if threshold == float('inf'):
                return "PVPGOD Барахолки", 0
            
            needed = int(threshold - points)
            return title, needed
            
    return "PVPGOD Барахолки", 0

def save_duels():
    """Сохраняет игры в файл"""
    try:
        data_to_save = {}
        for k, v in ACTIVE_DUELS.items():
            game_copy = v.copy()
            
            if "lock" in game_copy: del game_copy["lock"]
            if "last_update" in game_copy: del game_copy["last_update"]
            
            data_to_save[k] = game_copy
            
        with open(DUELS_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка сохранения дуэлей: {e}")

def get_top_users():
    """Возвращает топ-5 по сообщениям и топ-5 по играм (wins+losses)"""
    try:
        cursor.execute('SELECT user_id, msg_count FROM users ORDER BY msg_count DESC LIMIT 5')
        top_chatters = cursor.fetchall()

        cursor.execute('SELECT user_id, (wins + losses) as games FROM users ORDER BY games DESC LIMIT 5')
        top_duelists = cursor.fetchall()
        
        return top_chatters, top_duelists
    except Exception:
        return [], []

ACTIVE_DUELS = load_duels()

#-------------------------------------------------------------------------------------------------------------------ОБЩИЕ ФУНКЦИИ

def get_video_url(url):
    ydl_opts = {'format': 'best[ext=mp4]', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info['url'], info['title']
        except:
            return None, None

async def log_to_owner(text):
    """Отправляет лог владельцу (с защитой от HTML-ошибок)"""
    print(f"LOG: {text}")
    try:
        safe_text = hd.quote(str(text))
        await bot.send_message(OWNER_ID, f"🤖 <b>SYSTEM LOG:</b>\n{safe_text}")
    except Exception as e:
        print(f"⚠️ Не удалось отправить лог: {e}")

async def delete_later(message: types.Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass

MORNING_VOICE_ID = "AwACAgIAAxkBAAOnaXymlPVFa4x2wuzZZ0nPOgyvDuIAAq-MAALP-uBL4TESKm_ZL344BA" 

async def send_morning_voice():
    try:
        await bot.send_voice(CHAT_ID, MORNING_VOICE_ID, caption="Просыпайтесь, Стражи...")
    except Exception as e:
        await log_to_owner(f"❌ Ошибка войса: {e}")

async def check_silence_loop():
    global LAST_MESSAGE_TIME, USED_LORE_FACTS
    while True:
        await asyncio.sleep(300) 
        
        if (datetime.now() - LAST_MESSAGE_TIME).total_seconds() > 3600:
            if len(USED_LORE_FACTS) >= len(LORE_FACTS):
                USED_LORE_FACTS = []

            available_indices = [i for i in range(len(LORE_FACTS)) if i not in USED_LORE_FACTS]
            
            if available_indices:
                idx = random.choice(available_indices)
                USED_LORE_FACTS.append(idx)
                fact = LORE_FACTS[idx]
                
                try:
                    TARGET_CHAT_ID = CHAT_ID 
                    await bot.send_message(TARGET_CHAT_ID, f"{fact}")
                    LAST_MESSAGE_TIME = datetime.now()
                except Exception as e:
                    await log_to_owner(f"❌ Ошибка отправки факта: {e}")

def extract_urls(text):
    url_regex = r"(?P<url>https?://[^\s]+)"
    return re.findall(url_regex, text)

def is_link_allowed(text, chat_username):
    urls = extract_urls(text)
    if not urls: return True
    for url in urls:
        is_whitelisted = any(domain in url for domain in ALLOWED_DOMAINS)
        is_telegram = "t.me/" in url or "telegram.me/" in url
        is_self_chat = False
        if is_telegram and chat_username:
            if chat_username in url: is_self_chat = True
        if not is_whitelisted and not is_self_chat:
            return False
    return True

async def verification_timer(chat_id: int, user_id: int, username: str, welcome_msg_id: int):
    """
    Таймер верификации:
    1. Ждет 3 минуты -> Шлет напоминание.
    2. Ждет еще 2 минуты (всего 5) -> Банит.
    """
    try:
        await asyncio.sleep(180) 
        
        remind_msg = await bot.send_message(
            chat_id,
            f"@{username}, эй, Страж! <b>Подтверди, что ты не бот</b>, иначе придется забанить! <tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji>",
            reply_to_message_id=welcome_msg_id
        )
        
        if user_id in PENDING_VERIFICATION:
            PENDING_VERIFICATION[user_id]['remind_msg_id'] = remind_msg.message_id

        await asyncio.sleep(120) 
        
        await bot.ban_chat_member(chat_id, user_id)
        
        await bot.send_message(
            chat_id, 
            f"<tg-emoji emoji-id='5260293700088511294'>🚫</tg-emoji> @{username} оказался одержимым Тьмой (Bot). Изгнан в пустоту."
        )
        
        try: await bot.delete_message(chat_id, welcome_msg_id)
        except: pass
        try: await bot.delete_message(chat_id, remind_msg.message_id)
        except: pass

    except asyncio.CancelledError:
        pass
    except Exception as e:
        await log_to_owner(f"❌ Ошибка таймера верификации: {e}")
    finally:
        if user_id in PENDING_VERIFICATION:
            del PENDING_VERIFICATION[user_id]

def update_msg_stats(user_id):
    """Увеличивает счетчик сообщений пользователя"""
    try:
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        cursor.execute('UPDATE users SET msg_count = msg_count + 1 WHERE user_id = ?', (user_id,))
        conn.commit()
    except Exception:
        pass

#-------------------------------------------------------------------------------------------------------------------ХЕНДЛЕРЫ

#-------------------------------------------------------------------------------------------------------------------СТАТА ЧАТА

# --- ОТПРАВКА ОТ ЛИЦА БОТА (С СОХРАНЕНИЕМ ЭМОДЗИ И ФОРМАТА) ---
@dp.message(Command("send"))
async def send_as_bot_command(message: types.Message, command: CommandObject):
    # 1. Проверка на владельца
    if message.from_user.id != OWNER_ID:
        return

    # 2. Если это REPLY (Ответ на сообщение)
    # Это самый надежный способ отправить что угодно (фото, стикер, голосовое, текст с эмодзи)
    if message.reply_to_message:
        try:
            # Определяем ID чата из аргумента (например /send main)
            target_arg = command.args.split()[0] if command.args else "main"
            
            target_id = CHAT_ID if target_arg.lower() == "main" else int(target_arg)
            
            # Копируем сообщение точь-в-точь
            await message.reply_to_message.copy_to(chat_id=target_id)
            await message.react([ReactionTypeEmoji(emoji="👌")])
        except Exception as e:
            await message.reply(f"❌ Ошибка (Reply): {e}")
        return

    # 3. Если это ОБЫЧНЫЙ ТЕКСТ (/send main Текст)
    if not command.args:
        await message.reply("Использование:\n1. Напиши сообщение, ответь на него и напиши <code>/send main</code>\n2. Или <code>/send main Текст</code>")
        return

    try:
        # Разделяем аргументы: "main Текст сообщения..."
        args_split = command.args.split(maxsplit=1)
        if len(args_split) < 2:
            await message.reply("Где текст сообщения?")
            return
            
        chat_arg = args_split[0]
        text_body = args_split[1]

        # Определяем ID чата
        target_id = CHAT_ID if chat_arg.lower() == "main" else int(chat_arg)

        # === МАГИЯ С ЭМОДЗИ (ENTITIES) ===
        # Нам нужно найти, где в оригинальном сообщении начинается text_body,
        # чтобы правильно скопировать форматирование.
        
        full_text = message.text
        # Находим индекс начала текста (после команды и ID чата)
        offset = full_text.find(text_body)
        
        new_entities = []
        if message.entities:
            for entity in message.entities:
                # Если форматирование (жирный/эмодзи) находится внутри нашего текста
                if entity.offset >= offset:
                    # Создаем копию сущности, но сдвигаем её начало
                    # (потому что мы отрезали начало сообщения "/send main ")
                    new_ent = entity.model_copy()
                    new_ent.offset = entity.offset - offset
                    new_entities.append(new_ent)

        # Отправляем с сохранением премиум-эмодзи
        await bot.send_message(target_id, text_body, entities=new_entities)
        await message.react([ReactionTypeEmoji(emoji="👌")])

    except Exception as e:
        await message.reply(f"❌ Не удалось отправить: {e}")

@dp.message(Command("chats"))
async def list_chats_command(message: types.Message):
    if message.from_user.id != OWNER_ID: return

    cursor.execute("SELECT chat_id, title FROM chats")
    rows = cursor.fetchall()
    
    if not rows:
        await message.reply("Я пока не запомнил ни одного чата (нужна активность).")
        return
        
    text = "<b>📋 Список моих чатов:</b>\n\n"
    for cid, title in rows:
        text += f"ID: <code>{cid}</code> | {title}\n"
        
    await message.reply(text)

@dp.message(Command("chat_stats"))
async def chat_stats_command(message: types.Message):
    top_chatters, top_duelists = get_top_users()
    
    text = "<tg-emoji emoji-id='5350305691942788490'>📈</tg-emoji> <b>СТАТИСТИКА ЧАТА</b>\n\n"
    
    text += "<tg-emoji emoji-id='5417915203100613993'>💬</tg-emoji> <b>Топ болтунов:</b>\n"
    for i, (uid, count) in enumerate(top_chatters):
        try:
            member = await bot.get_chat_member(message.chat.id, uid)
            name = member.user.first_name
        except:
            name = "Неизвестный"
        text += f"{i+1}. {name} — {count} сообщ.\n"
        
    text += "\n<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> <b>Топ дуэлянтов:</b>\n"
    for i, (uid, games) in enumerate(top_duelists):
        try:
            member = await bot.get_chat_member(message.chat.id, uid)
            name = member.user.first_name
        except:
            name = "Неизвестный"
        text += f"{i+1}. {name} — {games} дуэлей.\n"
        
    await message.reply(text)
    
    asyncio.create_task(delete_later(message, 5))

#-------------------------------------------------------------------------------------------------------------------ВЫЗОВ (ПИНГ)
@dp.message(Command("newtag"))
async def new_tag_command(message: types.Message, command: CommandObject):
    # Проверка на админа
    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user_status.status not in ["administrator", "creator"] and message.from_user.id != OWNER_ID:
        return

    tag = command.args
    if not tag: return
    tag = tag.lower().replace("#", "")

    try:
        cursor.execute("INSERT OR IGNORE INTO allowed_tags (tag_name) VALUES (?)", (tag,))
        conn.commit()
        await message.reply(f"<tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> Тег <b>#{tag}</b> создан! Теперь на него можно подписаться.")
    except: pass

# ПОДПИСКА НА ТЕГ
@dp.message(Command("tag"))
async def tag_subscribe_command(message: types.Message, command: CommandObject):
    tag = command.args
    if not tag:
        # Если тег не указан — покажем список
        cursor.execute("SELECT tag_name FROM allowed_tags")
        rows = cursor.fetchall()
        tags_list = ", ".join([f"#{r[0]}" for r in rows])
        msg = await message.reply(f"Доступные теги:\n{tags_list}\n\nПиши <code>/tag название</code>")
        asyncio.create_task(delete_later(msg, 60))
        return
    
    tag = tag.lower().replace("#", "")
    
    # ПРОВЕРКА: Существует ли тег?
    cursor.execute("SELECT 1 FROM allowed_tags WHERE tag_name = ?", (tag,))
    if not cursor.fetchone():
        msg = await message.reply("<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Такого тега нет. Попроси админа создать его.")
        asyncio.create_task(delete_later(msg, 5))
        return
    
    # Подписка
    cursor.execute("INSERT OR IGNORE INTO tags (tag_name, user_id) VALUES (?, ?)", (tag, message.from_user.id))
    conn.commit()
    msg = await message.reply(f"<tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> Ты подписался на <b>#{tag}</b>.")
    asyncio.create_task(delete_later(msg, 300))

@dp.message(Command("call"))
async def tag_call_command(message: types.Message, command: CommandObject):
    tag = command.args
    if not tag:
        msg = await message.reply("Кого звать? Пример: `/call raid`")
        asyncio.create_task(delete_later(msg, 10))
        return
        
    tag = tag.lower().replace("#", "")
    
    cursor.execute("SELECT user_id FROM tags WHERE tag_name = ?", (tag,))
    users = cursor.fetchall()
    
    if not users:
        msg = await message.reply(f"Никто не подписан на #{tag}.")
        asyncio.create_task(delete_later(msg, 5))
        return
        
    # Формируем список меншенов (скрытых ссылок)
    mentions = []
    for (uid,) in users:
        try:
            # Получаем имя из основной таблицы users
            cursor.execute("SELECT name FROM users WHERE user_id = ?", (uid,))
            res = cursor.fetchone()
            name = res[0] if res else "Страж"
            mentions.append(f"<a href='tg://user?id={uid}'>{name}</a>")
        except: pass
        
    text = f"<tg-emoji emoji-id='5379748062124056162'>❗️</tg-emoji> <b>ВЫЗОВ #{tag.upper()}!</b>\n" + ", ".join(mentions)
    await message.reply(text)

@dp.message(Command("untag"))
async def tag_unsubscribe_command(message: types.Message, command: CommandObject):
    tag = command.args
    if not tag:
        msg = await message.reply("От чего отписаться? Пример: `/untag raid`")
        asyncio.create_task(delete_later(msg, 10))
        return
    
    tag = tag.lower().replace("#", "")
    user_id = message.from_user.id
    
    try:
        cursor.execute("DELETE FROM tags WHERE tag_name = ? AND user_id = ?", (tag, user_id))
        conn.commit()
        
        # Проверяем, удалилось ли что-то (rowcount)
        if cursor.rowcount > 0:
            msg = await message.reply(f"❌ Ты отписался от тега <b>#{tag}</b>.")
            asyncio.create_task(delete_later(msg, 30))
        else:
            msg = await message.reply(f"Ты и не был подписан на #{tag}.")
            asyncio.create_task(delete_later(msg, 5))
            
    except Exception as e:
        await log_to_owner(f"Ошибка untag: {e}")

#-------------------------------------------------------------------------------------------------------------------ТЕНЕВОЙ МУТ
@dp.message(Command("amute"))
async def amute_command(message: types.Message):
    try: await message.delete()
    except: pass

    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user_status.status not in ["administrator", "creator"]:
        return

    if not message.reply_to_message:
        msg = await message.answer("<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> Ответь на сообщение того, кого хочешь заглушить.")
        asyncio.create_task(delete_later(msg, 5))
        return

    target = message.reply_to_message.from_user
    target_id = target.id
    name = target.first_name

    if target_id == message.from_user.id:
        msg = await message.answer("<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> Зачем ты хочешь заглушить себя? Не делай этого.")
        asyncio.create_task(delete_later(msg, 5))
        return

    if target_id not in SILENT_MODE_USERS:
        SILENT_MODE_USERS.append(target_id)
        await message.answer(f"<tg-emoji emoji-id='5260293700088511294'>🚫</tg-emoji> <b>{name}</b> отправлен в теневой бан. Его сообщения будут исчезать.")
    else:
        msg = await message.answer(f"{name} уже в муте.")
        asyncio.create_task(delete_later(msg, 5))

@dp.message(Command("unamute"))
async def unamute_command(message: types.Message):
    try: await message.delete()
    except: pass

    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user_status.status not in ["administrator", "creator"]:
        return

    if not message.reply_to_message:
        return

    target_id = message.reply_to_message.from_user.id
    name = message.reply_to_message.from_user.first_name

    if target_id in SILENT_MODE_USERS:
        SILENT_MODE_USERS.remove(target_id)
        msg = await message.answer(f"<tg-emoji emoji-id='5395444784611480792'>✏️</tg-emoji> <b>{name}</b> снова слышен.")
        asyncio.create_task(delete_later(msg, 10))
    else:
        msg = await message.answer(f"{name} не был в муте.")
        asyncio.create_task(delete_later(msg, 5))

#-------------------------------------------------------------------------------------------------------------------ЗАПУСК ТУРНИРА (OWNER_ID)
@dp.message(Command("startcup"))
async def start_cup_command(message: types.Message, command: CommandObject):

    if message.from_user.id != OWNER_ID:
        return

    args = command.args
    if not args or not args.isdigit():
        await message.reply("<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> Укажи количество участников. Пример: `/startcup 8`")
        return

    count = int(args)
    
    global TOURNAMENT_ACTIVE, TOURNAMENT_MAX_PLAYERS, TOURNAMENT_PLAYERS, TOURNAMENT_USERNAMES
    TOURNAMENT_ACTIVE = True
    TOURNAMENT_MAX_PLAYERS = count
    TOURNAMENT_PLAYERS = []
    TOURNAMENT_USERNAMES = []

    await message.answer(
        f"<b><tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> РЕГИСТРАЦИЯ НА ТУРНИР ОТКРЫТА!</b>\n\n"
        f"Нужно стражей: {count}\n"
        f"Чтобы участвовать, напиши команду: <code>/cup</code>."
    )

#-------------------------------------------------------------------------------------------------------------------РЕГИСТРАЦИЯ (/cup)
@dp.message(Command("cup"))
async def join_cup_command(message: types.Message):
    global TOURNAMENT_ACTIVE, TOURNAMENT_PLAYERS, TOURNAMENT_USERNAMES

    if not TOURNAMENT_ACTIVE:
        msg = await message.reply("<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> Сейчас не ведется набор в турнир.")
        asyncio.create_task(delete_later(msg, 5))
        asyncio.create_task(delete_later(message, 5))
        return

    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

    if user_id in TOURNAMENT_PLAYERS:
        msg = await message.reply("<tg-emoji emoji-id='5395444784611480792'>✏️</tg-emoji> Ты уже в списке, Страж.")
        asyncio.create_task(delete_later(msg, 5))
        return

    TOURNAMENT_PLAYERS.append(user_id)
    TOURNAMENT_USERNAMES.append(username)
    
    current_count = len(TOURNAMENT_PLAYERS)
    needed = TOURNAMENT_MAX_PLAYERS

    if current_count < needed:
        await message.answer(f"<tg-emoji emoji-id='5395444784611480792'>✏️</tg-emoji> {username} записан! ({current_count}/{needed})")
    else:
        TOURNAMENT_ACTIVE = False
        
        random.shuffle(TOURNAMENT_USERNAMES)
        
        pairs_text = ""
        pair_num = 1
        
        for i in range(0, len(TOURNAMENT_USERNAMES), 2):
            p1 = TOURNAMENT_USERNAMES[i]
            if i + 1 < len(TOURNAMENT_USERNAMES):
                p2 = TOURNAMENT_USERNAMES[i+1]
                pairs_text += f"<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> Пара {pair_num}: {p1} vs {p2}\n"
            else:
                pairs_text += f"<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> Без пары: {p1}.\n"
            pair_num += 1

        await message.answer(
            f"<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> <b>НАБОР ЗАКРЫТ! Стартовая сетка сформирована</b>.\n\n"
            f"{pairs_text}\n\n"
            f"Ждите инструкций от организатора!"
        )

#-------------------------------------------------------------------------------------------------------------------ОБНОВЛЕНИЕ БД (ЛС БОТА)
@dp.message(F.document)
async def upload_db_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    
    if message.document.file_name != "database.db":
        return

    await bot.download(message.document, destination=DB_PATH)
    await message.reply("✅ База данных успешно обновлена! Перезагружаю...", reply_markup=None)

#-------------------------------------------------------------------------------------------------------------------СТАТА В ДУЭЛЯХ
@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    user_id = target.id
    name = target.first_name

    data = get_user_data(user_id)
    
    wins = data.get('wins', 0)
    losses = data.get('losses', 0)
    points = data.get('points', 0)
    total_games = wins + losses
    winrate = round((wins / total_games) * 100, 1) if total_games > 0 else 0.0
    rank_title, points_needed = get_rank_info(points)
    
    classes = {
        "<tg-emoji emoji-id='5330515960111583947'>🐍</tg-emoji> Хантер": data.get('class_hunter', 0),
        "<tg-emoji emoji-id='5330564987163267533'>🦅</tg-emoji> Варлок": data.get('class_warlock', 0),
        "<tg-emoji emoji-id='5330353116426551101'>🦁</tg-emoji> Титан": data.get('class_titan', 0)
    }
    fav_class = max(classes, key=classes.get)
    if classes[fav_class] == 0: fav_class = "Не определен"

    weapons = {
        "<tg-emoji emoji-id='5244894167863166109'>🃏</tg-emoji> Ace of Spades": data.get('w_ace', 0),
        "<tg-emoji emoji-id='5472003139303409777'>🤠</tg-emoji> Last Word": data.get('w_lw', 0),
        "<tg-emoji emoji-id='5471959145953396609'>🔥</tg-emoji> Golden Gun": data.get('w_gg', 0),
        "<tg-emoji emoji-id='5469821755478547431'>🔮</tg-emoji> Nova Bomb": data.get('w_nova', 0),
        "<tg-emoji emoji-id='5472214494644045946'>⚡️</tg-emoji> ThunderCrash": data.get('w_crash', 0)
    }
    fav_weapon = max(weapons, key=weapons.get)
    if weapons[fav_weapon] == 0: fav_weapon = "Кулаки"

    if points_needed > 0:
        next_rank_str = f"<tg-emoji emoji-id='5416117059207572332'>➡️</tg-emoji> <b>До повышения:</b> {points_needed} очков"
    else:
        next_rank_str = "<tg-emoji emoji-id='5357107601584693888'>👑</tg-emoji> <b>Максимальный ранг</b>"

    d = message.from_user
    du = f"@{d.username}"
    
    text = (
        f"<tg-emoji emoji-id='5434144690511290129'>📰</tg-emoji> <b>ДОСЬЕ ГОРНИЛА:</b> {du}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"<tg-emoji emoji-id='5238027455754680851'>🎖</tg-emoji> <b>Ранг:</b> {rank_title} ({points} очков)\n"
        f"{next_rank_str}\n"
        f"<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> <b>Матчей:</b> {total_games}\n"
        f"✅ <b>Побед:</b> {wins}\n"
        f"❌ <b>Поражений:</b> {losses}\n"
        f"<tg-emoji emoji-id='5244837092042750681'>📈</tg-emoji> <b>Винрейт:</b> {winrate}%\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"<tg-emoji emoji-id='5312138559556164615'>❤️</tg-emoji> <b>Класс:</b> {fav_class}\n"
        f"<tg-emoji emoji-id='5312138559556164615'>❤️</tg-emoji> <b>Револьвер:</b> {fav_weapon}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"<i>Шакс наблюдает за тобой.</i>"
    )
    
    msg = await message.reply(text)
    asyncio.create_task(delete_later(msg, 60))

#-------------------------------------------------------------------------------------------------------------------КОМАНДА /HELP
@dp.message(Command("help"))
async def help_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Гайд по боту", url=BOT_GUIDE)]
    ])
    msg = await message.answer(
        "Made by yagraze, pan1q & fimgreen.\n"
        "<tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji> ЖМИ <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        reply_markup=keyboard
    )
    asyncio.create_task(delete_later(msg, 15))
    asyncio.create_task(delete_later(message, 5))

#-------------------------------------------------------------------------------------------------------------------(РАНДОМ ОТВЕТ БОТА)
    VETERAN_PROMPT = (
    "Ты — ветеран Destiny 2 с 10,000 часов игры. Ты закрывал рейды в первый день, у тебя все печати и экзоты. "
    "Ты смотришь на чат с легким презрением и сарказмом. "
    "Твоя задача — очень кратко прокомментировать сообщение пользователя, как будто он нуб, но при этом дать понять, что ты круче. "
    "Можешь использовать сленг игры, но не злоупотребляй им. "
    "Будь дерзким, но смешным."
)
    if not message.text.startswith("/") and random.randint(1, 100) == 1:
        try:
            await bot.send_chat_action(message.chat.id, action="typing")
            
            response = await client.chat.completions.create(
                model="sonar",
                messages=[
                    {"role": "system", "content": VETERAN_PROMPT},
                    {"role": "user", "content": f"Сообщение стража: {message.text}"}
                ],
                temperature=1,
                max_tokens=100
            )
            
            vet_reply = response.choices[0].message.content
            await message.reply(vet_reply)
            
        except Exception as e:
            await log_to_owner(f"❌ Ошибка Ошибка Ветерана: {e}")

#-------------------------------------------------------------------------------------------------------------------КОМАНДА /SUMMARY
@dp.message(Command("summary"))
async def summary_command(message: types.Message):
    global SUMMARY_COOLDOWN_TIME
    
    now = datetime.now()
    if now < SUMMARY_COOLDOWN_TIME:
        time_left = SUMMARY_COOLDOWN_TIME - now
        minutes_left = int(time_left.total_seconds() // 60) + 1
        
        msg = await message.reply(
            f"Подожди, я уже недавно рассказывал что было в чате. "
            f"Обратись через <b>{minutes_left} мин</b>, а я пока почитаю логи. <tg-emoji emoji-id='5469629323763796670'>🙄</tg-emoji>"
        )
        asyncio.create_task(delete_later(msg, 10))
        asyncio.create_task(delete_later(message, 5))
        return

    chat_id = message.chat.id
    history = CHAT_HISTORY.get(chat_id, [])
    
    if len(history) < 5:
        msg = await message.answer("Архивы пусты. В этом чате тишина.")
        asyncio.create_task(delete_later(msg, 5))
        return

    history_text = "\n".join(history)
    summary_prompt = (
        "Ты — интеллектуальный ИИ-ассистент, специализирующийся на игре Destiny 2. По умолчанию интерпретируй ЛЮБОЙ вопрос в контексте Destiny 2, если явно не указано иное. НЕ ИСПОЛЬЗУЙ форматирование Telegram, по типу '**Жирность**', никаких выделений, ПИШИ ОБЫЧНЫМ ТЕКСТОМ ВСЕГДА, также НЕ ПИШИ в своих ответах «[2]» подобное, выглядит как указание источников, убирай это из своих ответов."
        "СТИЛЬ И ПОВЕДЕНИЕ: Пиши как опытный Страж, а не как справочник, Используй сленг комьюнити, но не перегибай, Не будь формальным без причины"
        "Твоя задача: прочитать лог чата и кратко пересказать, о чем говорили эти 'Стражи'. "
        "Выдели главные темы, посмейся над нытиками, если они есть, расскажи про чей-то срач, если он был. "
        "Будь краток (максимум 3-4 предложения)."
    )

    try:
        await bot.send_chat_action(message.chat.id, action="typing")
        
        response = await client.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": f"Вот лог чата:\n{history_text}"}
            ],
            temperature=0.8,
            max_tokens=300
        )
        
        summary = response.choices[0].message.content
        await message.reply(f"<b><tg-emoji emoji-id='5434144690511290129'>📰</tg-emoji> ОТЧЕТ НАБЛЮДЕНИЯ:</b>\n\n{summary}")
        
        SUMMARY_COOLDOWN_TIME = datetime.now() + timedelta(minutes=15)
        
    except Exception as e:
        await log_to_owner(f"❌ Ошибка Summary: {e}")
        msg = await message.reply("<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Сбой анализа данных. Архивы повреждены.")
        asyncio.create_task(delete_later(msg, 10))

#-------------------------------------------------------------------------------------------------------------------DUEL RPG
@dp.message(Command("duel"))
async def duel_command(message: types.Message, command: CommandObject):
    # Инициализация переменных
    attacker_id = 0
    defender_id = 0
    att_name = ""
    def_name = ""
    
    # 1. Сценарий АДМИНА: /duel @p1 @p2
    args = command.args
    admin_mode = False
    
    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if args and user_status.status in ["administrator", "creator"]:
        usernames = args.split()
        if len(usernames) >= 2:
            u1 = get_user_by_username(usernames[0])
            u2 = get_user_by_username(usernames[1])
            
            if u1 and u2:
                attacker_id = u1["id"]
                att_name = f"@{usernames[0].replace('@','').replace(',','')}" # Чистим от @ и запятых
                
                defender_id = u2["id"]
                def_name = f"@{usernames[1].replace('@','').replace(',','')}"
                
                admin_mode = True
            else:
                await message.reply("<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Кого-то из них нет в моей базе (пусть напишут что-нибудь в чат).")
                return
    
    # 2. Сценарий ОБЫЧНЫЙ: Ответ на сообщение
    if not admin_mode:
        if not message.reply_to_message:
            msg = await message.reply("<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> Чтобы вызвать на дуэль, ответь на сообщение соперника командой <code>/duel</code>.")
            asyncio.create_task(delete_later(msg, 5))
            return

        attacker = message.from_user
        defender = message.reply_to_message.from_user
        
        # Проверка на ботов (только в обычном режиме, т.к. есть объект User)
        if defender.is_bot or defender.id == 777000:
            msg = await message.reply("<tg-emoji emoji-id='5318773107207447403'>😱</tg-emoji> Ты вызываешь на бой саму Пустоту? Найди живого соперника.")
            asyncio.create_task(delete_later(msg, 5))
            return

        attacker_id = attacker.id
        defender_id = defender.id
        
        att_name = f"@{attacker.username}" if attacker.username else attacker.first_name
        def_name = f"@{defender.username}" if defender.username else defender.first_name

    # Общие проверки ID
    if defender_id == attacker_id:
        msg = await message.reply("Найди себе достойного противника (не себя) <tg-emoji emoji-id='5316850074255367258'>🤬</tg-emoji>.")
        asyncio.create_task(delete_later(msg, 5))
        return
    
    buttons = [
        [
            InlineKeyboardButton(text="✅ Принять вызов", callback_data=f"duel_start|{attacker_id}|{defender_id}"),
            InlineKeyboardButton(text="❌ Отказаться", callback_data=f"duel_decline|{attacker_id}|{defender_id}")
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    intro = f"<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> <b>ТУРНИРНЫЙ МАТЧ!</b> <tg-emoji emoji-id='5319018096436977294'>🔫</tg-emoji><tg-emoji emoji-id='5319002780583600195'>🔫</tg-emoji>\n\n" if admin_mode else f"<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> <b>ГОРНИЛО: ДУЭЛЬ!</b> <tg-emoji emoji-id='5319018096436977294'>🔫</tg-emoji><tg-emoji emoji-id='5319002780583600195'>🔫</tg-emoji>\n\n"
    
    await message.answer(
        f"{intro}"
        f"<b><tg-emoji emoji-id='5469797093776332017'>👤</tg-emoji> Страж №1:</b> {att_name}\n"
        f"<b><tg-emoji emoji-id='5469982881176653032'>👤</tg-emoji> Страж №2:</b> {def_name}\n\n"
        f"<b><tg-emoji emoji-id='5334544901428229844'>ℹ️</tg-emoji> Сетапы классов:</b>\n"
        f"<tg-emoji emoji-id='5330515960111583947'>🐍</tg-emoji> - Ханты: ГГ & Сияние;\n"
        f"<tg-emoji emoji-id='5330564987163267533'>🦅</tg-emoji> - Варлоки: Нова & Пожирание;\n"
        f"<tg-emoji emoji-id='5330353116426551101'>🦁</tg-emoji> - Титаны: ТКраш & Усиление.\n"
        f"<b><tg-emoji emoji-id='5334544901428229844'>ℹ️</tg-emoji> Оружие на выбор:</b>\n"
        f"<tg-emoji emoji-id='5244894167863166109'>🃏</tg-emoji> - Пиковый Туз;\n"
        f"<tg-emoji emoji-id='5472003139303409777'>🤠</tg-emoji> - Ластворд;\n"
        f"<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> - Шип.\n\n"
        f"<b>{def_name}</b>, ты принимаешь бой?",
        reply_markup=keyboard
    )

async def update_duel_message(callback: types.CallbackQuery, game_id):
    if game_id not in ACTIVE_DUELS:
        try: await callback.message.edit_reply_markup(reply_markup=None)
        except: pass
        return

    game = ACTIVE_DUELS[game_id]

    now = datetime.now()
    last = game.get("last_update", datetime.min)
    if (now - last).total_seconds() < 1.0:
        return
    
    game["last_update"] = now
    
    def get_hp_bar(hp):
        blocks = int(hp / 10) 
        return "▓" * blocks + "░" * (10 - blocks)

    p1 = game["p1"]
    p2 = game["p2"]
    
    current_player = p1 if game["turn"] == p1["id"] else p2
    current_class = current_player["class"]
    current_weapon = current_player["weapon"] # ace или lw
    current_name = current_player["name"]

    ru_classes = {"hunter": "<tg-emoji emoji-id='5330515960111583947'>🐍</tg-emoji>", "warlock": "<tg-emoji emoji-id='5330564987163267533'>🦅</tg-emoji>", "titan": "<tg-emoji emoji-id='5330353116426551101'>🦁</tg-emoji>"}
    title = f"{ru_classes[p1['class']]} vs {ru_classes[p2['class']]}"

    flying_status = ""
    if game.get("pending_crash"):
        flying_status = "\n<tg-emoji emoji-id='5456140674028019486'>⚡️</tg-emoji> <b>ВРАГ В ВОЗДУХЕ! СБЕЙ ЕГО!</b>"

    def_status = ""
    if p1["buff_def"] > 0: def_status += f"\n<tg-emoji emoji-id='5472175852823282918'>⚡️</tg-emoji> {p1['name']}: Щит {p1['buff_def']} HP"
    if p2["buff_def"] > 0: def_status += f"\n<tg-emoji emoji-id='5472175852823282918'>⚡️</tg-emoji> {p2['name']}: Щит {p2['buff_def']} HP"
    p1_status = ""
    if p1["poison_turns"] > 0: p1_status = " 🧪 (Яд)"
    p2_status = ""
    if p2["poison_turns"] > 0: p2_status = " 🧪 (Яд)"

    text = (
        f"<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> <b>{title}</b>\n\n"
        f"<tg-emoji emoji-id='5469797093776332017'>👤</tg-emoji> <b>{p1['name']}</b>: {p1['hp']} HP{p1_status}\n"
        f"[{get_hp_bar(p1['hp'])}]\n\n"
        f"<tg-emoji emoji-id='5469982881176653032'>👤</tg-emoji> <b>{p2['name']}</b>: {p2['hp']} HP{p2_status}\n"
        f"[{get_hp_bar(p2['hp'])}]\n\n"
        f"<tg-emoji emoji-id='5373251851074415873'>📝</tg-emoji> <i>Лог: {game['log']}</i>{flying_status}{def_status}\n\n"
        f"<b>— Ход:</b> {current_name} ({ru_classes[current_class]})"
    )

    if current_weapon == "ace":
        weapon_btn = InlineKeyboardButton(text="♠️ Ace (Crit)", callback_data="duel_shoot_primary")
    elif current_weapon == "lw":
        weapon_btn = InlineKeyboardButton(text="🤠 Last Word (Burst)", callback_data="duel_shoot_primary")
    elif current_weapon == "thorn":
        weapon_btn = InlineKeyboardButton(text="🧪 Thorn (DoT)", callback_data="duel_shoot_primary")

    buttons = []
    
    if current_class == "hunter":
        buttons = [
            [weapon_btn, InlineKeyboardButton(text="✨ Сияние (+Dmg)", callback_data="duel_buff_radiant")],
            [InlineKeyboardButton(text="🔥 Golden Gun (9%)", callback_data="duel_gg")]
        ]
    elif current_class == "warlock":
        buttons = [
            [weapon_btn, InlineKeyboardButton(text="🩸 Пожирание (+Heal)", callback_data="duel_buff_devour")],
            [InlineKeyboardButton(text="🔮 Nova Bomb (14%)", callback_data="duel_nova")]
        ]
    elif current_class == "titan":
        buttons = [
            [weapon_btn, InlineKeyboardButton(text="🛡 Усиление (Щит)", callback_data="duel_buff_amplify")],
            [InlineKeyboardButton(text="⚡️ Thundercrash (22%)", callback_data="duel_crash")]
        ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    refresh_btn = InlineKeyboardButton(text="🔄 Обновить (если зависло)", callback_data="duel_refresh")
    
    buttons.append([refresh_btn])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        if "Flood control" in str(e):
            await asyncio.sleep(1)
            try:
                await callback.message.edit_text(text, reply_markup=keyboard)
            except: pass
        pass

#-------------------------------------------------------------------------------------------------------------------ОБРАБОТКА ВЫБОРА (КЛАСС + ОРУЖИЕ)
@dp.callback_query(F.data.startswith("pick_"))
async def duel_class_handler(callback: types.CallbackQuery):
    game_id = callback.message.message_id
    if game_id not in ACTIVE_DUELS:
        await callback.answer("Матч устарел.", show_alert=True)
        return

    game = ACTIVE_DUELS[game_id]
    user_id = callback.from_user.id
    data = callback.data

    player_key = None
    if user_id == game["p1"]["id"]: player_key = "p1"
    elif user_id == game["p2"]["id"]: player_key = "p2"
    else:
        await callback.answer("Ты не участвуешь!", show_alert=True)
        return

    player = game[player_key]

#-------------------------------------------------------------------------------------------------------------------ЛОГИКА ВЫБОРА

    if data == "pick_full_random":
        if player["class"] and player["weapon"]:
            await callback.answer("Ты уже готов!", show_alert=True); return
        player["class"] = random.choice(["hunter", "warlock", "titan"])
        player["weapon"] = random.choice(["ace", "lw"])
        await callback.answer("Случайный билд выбран!")

    elif "pick_class" in data:
        cls = data.split("_")[2]
        player["class"] = cls
        await callback.answer(f"Класс: {cls.capitalize()}")

    elif "pick_weapon" in data:
        wpn = data.split("_")[2] # ace/lw
        if not player["class"]:
            await callback.answer("Сначала выбери класс!", show_alert=True)
            return
        player["weapon"] = wpn
        await callback.answer(f"Оружие: {wpn.capitalize()}")

#-------------------------------------------------------------------------------------------------------------------ОБНОВЛЕНИЕ СТАТУСА
    
    def get_status(p):
        if not p["class"]: return "Выбирает класс..."
        if not p["weapon"]: return f"{p['class'].capitalize()} (Выбирает оружие...)"
        return "<tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> ГОТОВ"

    if game["p1"]["class"] and game["p1"]["weapon"] and \
       game["p2"]["class"] and game["p2"]["weapon"]:
        
        game["state"] = "fighting"
        game["turn"] = random.choice([game["p1"]["id"], game["p2"]["id"]])

        update_usage(game["p1"]["id"], f"class_{game['p1']['class']}")
        update_usage(game["p2"]["id"], f"class_{game['p2']['class']}")

        ru_classes = {"hunter": "Хантер", "warlock": "Варлок", "titan": "Титан"}
           
        c1 = game["p1"]["class"]
        c2 = game["p2"]["class"]
        game["log"] = f"<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> {c1.upper()} vs {c2.upper()}! Бой начинается!"
        
        await update_duel_message(callback, game_id)
    else:
        text = (
            f"<tg-emoji emoji-id='5442864698187856287'>👜</tg-emoji> <b>ВЫБОР СНАРЯЖЕНИЯ</b>\n\n"
            f"<tg-emoji emoji-id='5469797093776332017'>👤</tg-emoji> <b>{game['p1']['name']}:</b> {get_status(game['p1'])}\n"
            f"<tg-emoji emoji-id='5469982881176653032'>👤</tg-emoji> <b>{game['p2']['name']}:</b> {get_status(game['p2'])}\n\n"
            f"1. Выбери Класс\n2. Выбери Оружие"
        )
        try: await callback.message.edit_text(text, reply_markup=callback.message.reply_markup)
        except: pass
        
    await callback.answer()

@dp.callback_query(F.data == "duel_refresh")
async def duel_refresh_handler(callback: types.CallbackQuery):
    game_id = callback.message.message_id
    if game_id not in ACTIVE_DUELS:
        await callback.answer("Попытка восстановить...", show_alert=True)
        return
        
    await update_duel_message(callback, game_id)
    await callback.answer("Интерфейс обновлен.")

@dp.callback_query(F.data.startswith("duel_"))
async def duel_handler(callback: types.CallbackQuery):
    data_parts = callback.data.split("|")
    action = data_parts[0]

    if action == "duel_decline":
        attacker_id = int(data_parts[1])
        defender_id = int(data_parts[2])
        user_id = callback.from_user.id
        
        if user_id != defender_id and user_id != attacker_id:
            await callback.answer("Не лезь, это не твой бой!", show_alert=True)
            return

        if user_id == attacker_id:
            await callback.message.edit_text(f"<tg-emoji emoji-id='5445267414562389170'>🗑</tg-emoji> <b>Вызов отозван.</b> Дуэль удалена.")
            return

        if user_id == defender_id:
            await callback.message.edit_text(f"<tg-emoji emoji-id='5445267414562389170'>🗑</tg-emoji> <b>Вызов отклонён.</b> Дуэль удалена.")
            return
    
    game_id = callback.message.message_id
    
    if game_id not in ACTIVE_DUELS:
        try:
            saved_duels = load_duels()
            if game_id in saved_duels:
                ACTIVE_DUELS[game_id] = saved_duels[game_id]
                print(f"🔄 Игра {game_id} восстановлена из файла.")
        except: pass

    if action != "duel_start" and game_id not in ACTIVE_DUELS:
        await callback.answer("Игра не найдена (удалена или устарела).", show_alert=True)
        try: await callback.message.edit_text("<tg-emoji emoji-id='5445267414562389170'>🗑</tg-emoji> <b>Матч удалён.</b>", reply_markup=None)
        except: pass
        return

#-------------------------------------------------------------------------------------------------------------------СТАРТ
    if action == "duel_start":
        attacker_id = int(data_parts[1])
        defender_id = int(data_parts[2])
        if callback.from_user.id != defender_id:
            await callback.answer("Жди решения соперника!", show_alert=True)
            return

        game_id = callback.message.message_id
        
        try:
            att_m = await bot.get_chat_member(callback.message.chat.id, attacker_id)
            def_m = await bot.get_chat_member(callback.message.chat.id, defender_id)
            att_name = f"@{att_m.user.username}" if att_m.user.username else att_m.user.first_name
            def_name = f"@{def_m.user.username}" if def_m.user.username else def_m.user.first_name
        except:
            att_name, def_name = "Игрок 1", "Игрок 2"

        ACTIVE_DUELS[game_id] = {
            "p1": {
                "id": attacker_id, "name": att_name, "hp": 100, 
                "class": None, "weapon": None, # Новое поле
                "ace_streak": 0, "poison_turns": 0, "buff_dmg": 0, "buff_heal": False, "buff_def": 0
            },
            "p2": {
                "id": defender_id, "name": def_name, "hp": 100, 
                "class": None, "weapon": None, # Новое поле
                "ace_streak": 0, "poison_turns": 0, "buff_dmg": 0, "buff_heal": False, "buff_def": 0
            },
            "state": "choosing_class",
            "log": "<tg-emoji emoji-id='5442864698187856287'>👜</tg-emoji> Ожидание выбора снаряжения...",
            "lock": asyncio.Lock()
        }

        buttons = [
            [
                InlineKeyboardButton(text="🐍 Хантер", callback_data="pick_class_hunter"),
                InlineKeyboardButton(text="🔮 Варлок", callback_data="pick_class_warlock"),
                InlineKeyboardButton(text="🛡 Титан", callback_data="pick_class_titan")
            ],
            [
                InlineKeyboardButton(text="♠️ Ace of Spades", callback_data="pick_weapon_ace"),
                InlineKeyboardButton(text="🤠 Last Word", callback_data="pick_weapon_lw"),
                InlineKeyboardButton(text="🧪 Thorn", callback_data="pick_weapon_thorn")
            ],
            [InlineKeyboardButton(text="🎲 Случайный билд", callback_data="pick_full_random")]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        text = (
            f"<tg-emoji emoji-id='5442864698187856287'>👜</tg-emoji> <b>ВЫБОР СНАРЯЖЕНИЯ</b>\n\n"
            f"<tg-emoji emoji-id='5469797093776332017'>👤</tg-emoji> <b>{att_name}:</b> Выбор...\n"
            f"<tg-emoji emoji-id='5469982881176653032'>👤</tg-emoji> <b>{def_name}:</b> Выбор...\n\n"
            f"1. Выбери Класс\n2. Выбери Оружие"
        )

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return

#-------------------------------------------------------------------------------------------------------------------БАФФЫ (АБИЛКИ)
    if action in ["duel_buff_radiant", "duel_buff_devour", "duel_buff_amplify"]:
        game_id = callback.message.message_id
        if game_id not in ACTIVE_DUELS: return
        game = ACTIVE_DUELS[game_id]
        
        async with game["lock"]:
            if callback.from_user.id != game["turn"]:
                await callback.answer("Не твой ход!", show_alert=True)
                return

            if callback.from_user.id == game["p1"]["id"]:
                caster, enemy = game["p1"], game["p2"]
            else:
                caster, enemy = game["p2"], game["p1"]

            buff_name = ""
            log_msg = ""
            
            if action == "duel_buff_radiant" and caster["class"] == "hunter":
                caster["buff_dmg"] = 10
                buff_name = "💥 Сияние"
                log_msg = f"{caster['name']} активирует <tg-emoji emoji-id='5472158054478810637'>💥</tg-emoji> <b>Сияние</b>! След. выстрел +10 урона."
                save_duels()
            elif action == "duel_buff_devour" and caster["class"] == "warlock":
                caster["buff_heal"] = True
                buff_name = "🩸 Пожирание"
                log_msg = f"{caster['name']} активирует <tg-emoji emoji-id='5474317667114457231'>🩸</tg-emoji> <b>Пожирание</b>! След. попадание исцелит 10 HP."
                save_duels()
            elif action == "duel_buff_amplify" and caster["class"] == "titan":
                caster["buff_def"] = 10
                buff_name = "⚡️ Усиление"
                log_msg = f"{caster['name']} получает <tg-emoji emoji-id='5472175852823282918'>⚡️</tg-emoji> <b>Усиление</b>! След. урон по нему снижен на 10."
                save_duels()
            else:
                await callback.answer("Не твой класс!", show_alert=True)
                return

            # ТИК ЯДА + КОМБО С БАФФОМ
            if enemy["poison_turns"] > 0:
                poison_dmg = 9
                
                # 1. КОМБО С СИЯНИЕМ (Если только что включили или висело)
                if caster["buff_dmg"] > 0:
                    poison_dmg += caster["buff_dmg"]
                    caster["buff_dmg"] = 0 # Сгорает
                    log_msg += f"\n<tg-emoji emoji-id='5472158054478810637'>💥</tg-emoji> <b>СИЯЮЩИЙ ЯД!</b> ({poison_dmg} урона)"
                else:
                    log_msg += f"\n<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> Яд сжигает {target['name']} (-9 HP)!"

                # 2. КОМБО С ПОЖИРАНИЕМ
                if caster["buff_heal"]:
                    caster["hp"] += 10
                    if caster["hp"] > 100: caster["hp"] = 100
                    caster["buff_heal"] = False # Сгорает
                    log_msg += " (<tg-emoji emoji-id='5474317667114457231'>🩸</tg-emoji> +10 HP)"

                # Наносим урон
                enemy["hp"] -= poison_dmg
                enemy["poison_turns"] -= 1
                
                # Проверка смерти
                if enemy["hp"] <= 0:
                    enemy["hp"] = 0
                    update_duel_stats(caster['id'], True); update_duel_stats(enemy['id'], False)
                    del ACTIVE_DUELS[game_id]; save_duels()
                    await callback.message.edit_text(f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> {enemy['name']} погиб от яда!", reply_markup=None)
                    await callback.answer(); return
            
            flying_titan_id = game.get("pending_crash")
            if flying_titan_id:
                game["crash_turns"] -= 1
                if game["crash_turns"] <= 0:
                    titan_id = flying_titan_id
                    titan = game["p1"] if game["p1"]["id"] == titan_id else game["p2"]
                    enemy_player = game["p1"] if game["p1"]["id"] != titan_id else game["p2"] # переименовал, чтобы не конфликтовало
                    
                    game["pending_crash"] = None
                    
                    if random.randint(1, 100) <= 17:
                        caster["hp"] = 0
                        update_duel_stats(titan['id'], True)
                        update_duel_stats(caster['id'], False)
                        del ACTIVE_DUELS[game_id]
                        msg = f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n<tg-emoji emoji-id='5456140674028019486'>⚡️</tg-emoji> <b>БУУУМ!</b> {titan['name']} приземляется на тебя! (-100 HP)"
                        await callback.message.edit_text(msg, reply_markup=None)
                        await callback.answer()
                        return
                    else:
                        log_msg += f"\n\n<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> {titan['name']} промахивается ультой!"
                        game["turn"] = titan_id
                else:
                    log_msg += "\n<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> Титан летит! Остался 1 ход!"
                    game["turn"] = caster["id"]
            else:
                game["turn"] = enemy["id"]

            game["log"] = log_msg
            save_duels()
            await update_duel_message(callback, game_id)
            await callback.answer(f"{buff_name} активировано!")
            return

#-------------------------------------------------------------------------------------------------------------------ВЫСТРЕЛ (ОСНОВНОЙ И УЛЬТА)
    if action in ["duel_shoot_primary", "duel_gg", "duel_nova", "duel_crash"]:
        game_id = callback.message.message_id
        if game_id not in ACTIVE_DUELS: return
        game = ACTIVE_DUELS[game_id]

        async with game["lock"]:
            if game.get("state") != "fighting":
                await callback.answer("Не все готовы!", show_alert=True); return

            if game.get("pending_crash") and action == "duel_crash":
                await callback.answer("Враг летит! Сбей его!", show_alert=True); return

            shooter_id = callback.from_user.id
            if shooter_id != game["turn"]:
                await callback.answer("Не твой ход!", show_alert=True); return

            if shooter_id == game["p1"]["id"]:
                shooter, target = game["p1"], game["p2"]
            else:
                shooter, target = game["p2"], game["p1"]

            cls = shooter["class"]
            
            if cls == "hunter" and action in ["duel_nova", "duel_crash"]:
                await callback.answer("Это не твоя способность!", show_alert=True); return
                
            if cls == "warlock" and action in ["duel_gg", "duel_crash"]:
                await callback.answer("Это не твоя способность!", show_alert=True); return
                
            if cls == "titan" and action in ["duel_gg", "duel_nova"]:
                await callback.answer("Это не твоя способность!", show_alert=True); return
            
            damage = 0
            hits_count = 0
            log_msg = ""
            healed_amount = 0
            
#-------------------------------------------------------------------------------------------------------------------ЛОГИКА ОРУЖИЯ

            if action == "duel_shoot_primary":
                weapon_type = shooter["weapon"]
                
                if weapon_type == "ace":
                    update_usage(shooter_id, "w_ace")
                    weapon_name = "<tg-emoji emoji-id='5244894167863166109'>🃏</tg-emoji> Пиковый Туз"
                    shooter["ace_streak"] = shooter.get("ace_streak", 0)
                    
                    base_chance = 50
                    crit_chance = 10 if shooter["ace_streak"] == 1 else 0
                    
                    roll = random.randint(1, 100)
                    
                    if roll <= crit_chance:
                        damage = 50
                        shooter["ace_streak"] = 0
                        log_msg = f"<tg-emoji emoji-id='5276032951342088188'>💥</tg-emoji> <b>MEMENTO MORI!</b> {shooter['name']} критует Тузом на {damage}!"
                    elif roll <= (crit_chance + base_chance):
                        damage = 25
                        shooter["ace_streak"] = 1
                        log_msg = f"<tg-emoji emoji-id='5379748062124056162'>❗️</tg-emoji> <b>Попадание!</b> {shooter['name']} наносит Тузом {damage} урона."
                    else:
                        damage = 0
                        shooter["ace_streak"] = 0
                        log_msg = f"<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> <b>Промах!</b> {shooter['name']} мажет с Туза."

                elif weapon_type == "lw":
                    update_usage(shooter_id, "w_lw")
                    weapon_name = "<tg-emoji emoji-id='5472003139303409777'>🤠</tg-emoji> Last Word"
                    shooter["ace_streak"] = 0
                    
                    shots_log = []
                    for _ in range(8):
                        if random.randint(1, 100) <= 34:
                            damage += 5
                            hits_count += 1
                            shots_log.append("💥")
                        else:
                            shots_log.append(" ")
                    
                    visual = "".join(shots_log)
                    if damage > 0:
                        if hits_count in [2, 3, 4]:
                            times_word = "раза"
                        else:
                            times_word = "раз"
                        log_msg = f"<tg-emoji emoji-id='5379748062124056162'>❗️</tg-emoji> <b>Попадание!</b> {shooter['name']} попадает {hits_count} {times_word}! ({damage} урона)\n\n[{visual}]"
                    else:
                        log_msg = f"<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> <b>Промах!</b> {shooter['name']} разрядил барабан в кактусы.\n[{visual}]"

                elif weapon_type == "thorn":
                    update_usage(shooter_id, "w_thorn")
                    weapon_name = "<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> Шип"
                    shooter["ace_streak"] = 0
                
                    if random.randint(1, 100) <= 50:
                        hit = True
                        damage = 20
                        
                        # Если яд уже был, он тикает ПЕРЕД обновлением
                        if target["poison_turns"] > 0:
                            damage += 9 # Добавляем тик яда к урону выстрела
                            log_msg = f"<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> <b>Попадание!</b> {shooter['name']} отравляет врага Шипом! (29 урона + Яд)"
                        else:
                            log_msg = f"<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> <b>Попадание!</b> {shooter['name']} отравляет врага Шипом! (20 урона + Яд)."
                            
                        target["poison_turns"] = 1 # Обновляем таймер
                    else:
                        hit = False
                        damage = 0
                        log_msg = f"<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> <b>Промах!</b> Шип пролетел мимо."
                
            elif action == "duel_gg":
                update_usage(shooter_id, "w_gg")
                if random.randint(1, 100) <= 9: damage = 100; log_msg = f"<tg-emoji emoji-id='5276032951342088188'>💥</tg-emoji> <b>КРИТ!</b> {shooter['name']} использует <tg-emoji emoji-id='5312241539987020022'>🔥</tg-emoji> Голден Ган! (100 урона)"
                else: log_msg = f"<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> {shooter['name']} промазал с Голден Гана!"
                
            elif action == "duel_nova":
                update_usage(shooter_id, "w_nova")
                roll = random.randint(1, 100)
                if roll <= 5: damage = 100; log_msg = f"<tg-emoji emoji-id='5276032951342088188'>💥</tg-emoji> <b>КРИТ!</b> {shooter['name']} взорвал соперника НОВОЙ! (100 урона)"
                elif roll <= 14: damage = 75; log_msg = f"<tg-emoji emoji-id='5379748062124056162'>❗️</tg-emoji> <b>НОВА!</b> {shooter['name']} задел соперника взрывом! (75 урона)"
                else: log_msg = f"<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> Нова улетела в стену."
                
            elif action == "duel_crash":
                update_usage(shooter_id, "w_crash")
                if game.get("pending_crash"): await callback.answer("Уже летит!", show_alert=True); return
                    
                # --- ТИК ЯДА ПЕРЕД ПОЛЕТОМ ---
                if target["poison_turns"] > 0:
                    target["hp"] -= 9
                    target["poison_turns"] -= 1
                    poison_msg = f"\n🧪 Яд сжигает {target['name']} (-9 HP)!"
                    if target["hp"] <= 0:
                        # (Победа Титана)
                        target["hp"] = 0
                        update_duel_stats(shooter['id'], True); update_duel_stats(target['id'], False)
                        del ACTIVE_DUELS[game_id]; save_duels()
                        await callback.message.edit_text(f"🏆 <b>ПОБЕДА!</b>{poison_msg}\n⚡ Титан улетел, а враг умер от яда.", reply_markup=None)
                        await callback.answer(); return
                else:
                    poison_msg = ""
                game["pending_crash"] = shooter_id 
                game["crash_turns"] = 2            
                game["turn"] = target["id"]        
                game["log"] = f"<tg-emoji emoji-id='5456140674028019486'>⚡️</tg-emoji> <b>ГРОМ!</b> {shooter['name']} прожал ульту! у соперника 2 действия!"
                save_duels() 
                await update_duel_message(callback, game_id)
                await callback.answer()
                return

#-------------------------------------------------------------------------------------------------------------------ПРИМЕНЕНИЕ БАФФОВ И УРОНА
            if damage > 0 and shooter["buff_dmg"] > 0:
                damage += shooter["buff_dmg"]
                shooter["buff_dmg"] = 0
                log_msg += " (<tg-emoji emoji-id='5472158054478810637'>💥</tg-emoji> +10 DMG)"

            if damage > 0 and damage < 100 and target["buff_def"] > 0:
                blocked = min(damage, target["buff_def"]) 
                
                damage -= blocked
                target["buff_def"] -= blocked
                
                log_msg += f" (<tg-emoji emoji-id='5472175852823282918'>⚡️</tg-emoji> -{blocked})"
                if target["buff_def"] <= 0:
                    log_msg += " [Щит сломан]"

            if damage > 0 and shooter["buff_heal"] and action == "duel_shoot_primary":
                shooter["hp"] += 10
                if shooter["hp"] > 100: shooter["hp"] = 100
                shooter["buff_heal"] = False # Сгорает
                log_msg += " (<tg-emoji emoji-id='5474317667114457231'>🩸</tg-emoji> +10 HP)"

            # 1. Наносим урон врагу
            if damage > 0:
                target["hp"] -= damage
                if target["hp"] < 0: target["hp"] = 0

            # 2. ТИК ЯДА (У врага, в МОЙ ход)
            # Но есть нюанс: если мы ТОЛЬКО ЧТО попали Шипом, яд не должен тикнуть мгновенно.
            # (По твоим словам: "попадаю, противник ходит, Я делаю ход - дот срабатывает").
            
            is_new_poison = (action == "duel_shoot_primary" and shooter["weapon"] == "thorn" and hit)
            
            if target["poison_turns"] > 0 and not is_new_poison:
                target["hp"] -= 9
                target["poison_turns"] -= 1
                log_msg += f"\n<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> Яд сжигает {target['name']} (-9 HP)!"
                if target["hp"] < 0: target["hp"] = 0

            # 3. ПРОВЕРКА ПОБЕДЫ (От выстрела ИЛИ от яда)
            if target["hp"] <= 0:
                update_duel_stats(shooter['id'], True)
                update_duel_stats(target['id'], False)
                del ACTIVE_DUELS[game_id]
                
                # Если умер от яда, а не выстрела, можно поменять текст, но победа все равно моя
                await callback.message.edit_text(f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> {target['name']} повержен.", reply_markup=None)
                await callback.answer()
                return

            flying_titan_id = game.get("pending_crash")
            if flying_titan_id:
                if shooter_id != flying_titan_id:
                    game["crash_turns"] -= 1
                    if game["crash_turns"] <= 0:
                        titan_id = flying_titan_id
                        titan = game["p1"] if game["p1"]["id"] == titan_id else game["p2"]
                        enemy_pl = game["p1"] if game["p1"]["id"] != titan_id else game["p2"]
                        game["pending_crash"] = None

                    # ТИК ЯДА (У защитника, если он отравлен)
                    if shooter["poison_turns"] > 0:
                        shooter["hp"] -= 9
                        shooter["poison_turns"] -= 1
                        log_msg += f"\n<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> Яд (-9 HP)"
                        
                        if random.randint(1, 100) <= 17:
                            enemy_pl["hp"] = 0
                            update_duel_stats(titan['id'], True)
                            update_duel_stats(enemy_pl['id'], False)
                            del ACTIVE_DUELS[game_id]
                            msg = f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n<tg-emoji emoji-id='5456140674028019486'>⚡️</tg-emoji> <b>БУУУМ!</b> {titan['name']} размазал соперника! (-100 HP)"
                            await callback.message.edit_text(msg, reply_markup=None)
                            await callback.answer()
                            return
                        else:
                            game["log"] = f"{log_msg}\n\n<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> {titan['name']} промахивается тандеркрашем!"
                            game["turn"] = titan_id
                    else:
                        game["log"] = f"{log_msg}\n<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> Титан летит! 1 выстрел остался!"
                        game["turn"] = shooter_id
            else:
                game["turn"] = target["id"]
                game["log"] = log_msg

            await update_duel_message(callback, game_id)
            await callback.answer()

#-------------------------------------------------------------------------------------------------------------------РЕПОРТ
@dp.message(Command("report"))
async def report_command(message: types.Message):

    if not message.reply_to_message:
        msg = await message.reply("<tg-emoji emoji-id='5260293700088511294'>🚫</tg-emoji> Используй команду в ответ на сообщение нарушителя.")
        asyncio.create_task(delete_later(msg, 5))
        return

    reported_msg = message.reply_to_message
    reporter = message.from_user.username or message.from_user.first_name
    violator = reported_msg.from_user.username or reported_msg.from_user.first_name

    if message.chat.username:
        msg_link = f"https://t.me/{message.chat.username}/{reported_msg.message_id}"
    else:
        chat_id_str = str(message.chat.id)
        if chat_id_str.startswith("-100"):
            clean_id = chat_id_str[4:] 
        else:
            clean_id = chat_id_str 
        msg_link = f"https://t.me/c/{clean_id}/{reported_msg.message_id}"

    report_text = (
        f"<tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> СИГНАЛ ТРЕВОГИ (РЕПОРТ)\n"
        f"<tg-emoji emoji-id='5395444784611480792'>✏️</tg-emoji> Донёс: @{reporter}\n"
        f"<tg-emoji emoji-id='5240241223632954241'>⛔️</tg-emoji> Нарушил: @{violator}\n\n"
        f"<tg-emoji emoji-id='5416117059207572332'>➡️</tg-emoji> {msg_link}"
    )

    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=report_text)
        confirm = await message.answer("<tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> Жалоба отправлена Авангарду.")
        asyncio.create_task(delete_later(confirm, 5))
        asyncio.create_task(delete_later(message, 1))
        
    except Exception as e:
        await log_to_owner(f"❌ Ошибка репорта: {e}")

#-------------------------------------------------------------------------------------------------------------------MUTE (ADMIN)
@dp.message(Command("mute"))
async def admin_mute_command(message: types.Message, command: CommandObject):
    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user_status.status not in ["administrator", "creator"]:
        return

    target_user = None
    mute_minutes = 15 

    args = command.args.split() if command.args else []
    for arg in args:
        if arg.isdigit():
            mute_minutes = int(arg)
            break
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif message.entities:
        for entity in message.entities:
            if entity.type == "text_mention":
                target_user = entity.user
                break
            elif entity.type == "mention":
                pass

    if not target_user:
        msg = await message.answer("<tg-emoji emoji-id='5260293700088511294'>🚫</tg-emoji> Чтобы выдать мут, отправь команду в ответ на сообщение нарушителя.\nПример: <code>/mute</code> 30")
        asyncio.create_task(delete_later(msg, 10))
        return

    target_status = await bot.get_chat_member(message.chat.id, target_user.id)
    if target_status.status in ["administrator", "creator"]:
        msg = await message.answer("<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Я не могу заглушить офицера Авангарда (Админа).")
        asyncio.create_task(delete_later(msg, 15))
        return

    try:
        unmute_time = datetime.now() + timedelta(minutes=mute_minutes)
        await message.chat.restrict(
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=unmute_time
        )

        username = target_user.username or target_user.first_name
        phrase = random.choice(ADMIN_MUTE_PHRASES).format(
            time=mute_minutes
        ).replace("@username", f"@{username}")
        await message.answer(phrase)
        asyncio.create_task(delete_later(message, 5))

    except Exception as e:
        await log_to_owner(f"❌ Ошибка мута: {e}")
        msg = await message.answer(f"Ошибка протокола: {e}")
        asyncio.create_task(delete_later(msg, 10))

@dp.message(Command("unmute"))
async def admin_unmute_command(message: types.Message):
    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user_status.status not in ["administrator", "creator"]:
        return 

    if not message.reply_to_message:
        msg = await message.reply("<tg-emoji emoji-id='5260293700088511294'>🚫</tg-emoji> Чтобы снять мут, сделай Reply (Ответить) на сообщение и напиши <code>/unmute</code>")
        asyncio.create_task(delete_later(msg, 10))
        return

    target_user = message.reply_to_message.from_user
    username = target_user.username or target_user.first_name

    try:
        await message.chat.restrict(
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_send_polls=True,
                can_add_web_page_previews=True
            ),
            until_date=datetime.now() 
        )
        text = random.choice(UNMUTE_PHRASES).replace("@username", f"@{username}")
        await message.answer(text)
        asyncio.create_task(delete_later(message, 5))

    except Exception as e:
        print(f"Ошибка размута: {e}")
        await log_to_owner(f"❌ Ошибка размута: {e}")
        msg = await message.answer("<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Не удалось снять мут. Возможно, я не админ?")
        asyncio.create_task(delete_later(msg, 10))

#-------------------------------------------------------------------------------------------------------------------LASTWORD (ROULETTE)
@dp.message(Command("lastword", "lw", "ластворд", "лв"))
async def mute_roulette(message: types.Message):
    bullet = random.randint(1, 4) 
    username = message.from_user.username or message.from_user.first_name

    if bullet == 1:
        user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user_status.status in ["administrator", "creator"]:
            msg = await message.reply("<tg-emoji emoji-id='5463156928307801722'>🤕</tg-emoji> Выстрел! Прямое попадание, но ты Админ с овершилдом. Живи.")
            return

        try:
            duration_roll = random.randint(1, 5)
            if duration_roll == 5:
                mute_duration = timedelta(minutes=30)
                phrase = random.choice(MUTE_CRITICAL_PHRASES).replace("@username", f"@{username}")
            else:
                mute_duration = timedelta(minutes=15)
                phrase = random.choice(MUTE_SHORT_PHRASES).replace("@username", f"@{username}")

            unmute_time = datetime.now() + mute_duration
            await message.chat.restrict(
                user_id=message.from_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=unmute_time
            )
            await message.reply(phrase)
            
        except Exception as e:
            await log_to_owner(f"❌ Ошибка рулетки: {e}")
            await message.reply("Хотел выдать мут, но не хватает прав админа! Проверь настройки.")
            print(f"Ошибка мута: {e}")

    else:
        text = random.choice(SAFE_PHRASES)
        msg = await message.reply(f"{text}")
        asyncio.create_task(delete_later(msg, 20))

#-------------------------------------------------------------------------------------------------------------------АВТОКОММЕНТ
@dp.message(F.is_automatic_forward)
async def auto_comment_channel_post(message: types.Message):
    if message.media_group_id:
        if message.media_group_id in PROCESSED_ALBUMS:
            return 
        PROCESSED_ALBUMS.append(message.media_group_id)
        if len(PROCESSED_ALBUMS) > 100:
            PROCESSED_ALBUMS.pop(0)
    
    try:
        await asyncio.sleep(1)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="‼️ Правила", url=LINK_RULES),
                InlineKeyboardButton(text="💬 Чат", url=LINK_CHAT)
            ]
        ])

        safe_text = "⏳ Загрузка навигации..."

        final_text = (
            "<b><tg-emoji emoji-id='5395444784611480792'>✏️</tg-emoji> Услуги:</b>\n\n"
            "• <a href='http://d2shop.ru/'>Магазин кодов</a> (Эмблемы, Шейдеры, Корабли, Сперроу, Эмоции)\n"
            "• <a href='https://d2shop.ru/klyuchi-steam'>Официальные ключи Steam</a>: Destiny, Marathon, и другие\n"
            "• <a href='https://d2shop.ru/uslugi-psn-xbox-egs-steam'>Услуги PSN, XBOX, EGS, STEAM</a> и другие\n"
            "• <a href='https://d2shop.ru/zakaz-mercha'>Заказ мерча по Destiny</a>, и не только\n"
            "• <a href='https://d2shop.ru/oplaty-servisov'>Оплаты сервисов, софта, подписок</a>\n"
            "• <a href='https://d2shop.ru/destiny-serebro'>Серебро</a>\n"
            "• <a href='https://d2shop.ru/dropy-mercha'>Дропы мерча</a>\n"
            "• <a href='https://vk.com/topic-213711546_48664680?offset=2060'>Отзывы о товарах и услугах</a>\n\n"
            "<tg-emoji emoji-id='5416117059207572332'>➡️</tg-emoji> <a href='https://t.me/llRGaming'>По любому вопросу/услуге</a>\n\n"
            "<b><tg-emoji emoji-id='5282843764451195532'>🖥</tg-emoji> Наши ресурсы:</b>\n"
            "• <a href='https://vk.com/destinygoods'>Группа VK</a>\n"
            "• <a href='http://t.me/destinygoods'>Канал ТГ</a>\n"
            "• <a href='https://discord.gg/nPZTHaSADz'>Дискорд Сервер</a> (Лор, Спойлеры, Мода)\n\n"
            "<b><tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> Кланы D2 (вступление открытое):</b>\n"
            "• <tg-emoji emoji-id='5472038418164785413'>1️⃣</tg-emoji> <a href='https://www.bungie.net/ru/ClanV2?groupid=5223067'>Baraholka Community Hub</a>\n"
            "• <tg-emoji emoji-id='5471895155235654649'>2️⃣</tg-emoji> <a href='https://www.bungie.net/en/ClanV2?groupid=5237071'>Baraholka United</a>\n\n"
            "<b><tg-emoji emoji-id='5373098009640836781'>📚</tg-emoji> Другое:</b>\n"
            "• <a href='https://d2shop.ru/emblems'>Универсальные коды эмблем</a>\n"
            "• <a href='https://d2shop.ru/links'>Полезные Destiny 2 сайты</a>\n"
            "• <a href='https://youtu.be/3Z9muUsJpEI?si=_ST2niN48Kmo_fZB'>Наше видео про Призрака</a>\n"
            "• <a href='http://telegra.ph/Baraholka-Bot-01-22'>Гайд по Боту и Дуэлям</a>\n\n"
            "<b><tg-emoji emoji-id='5467539229468793355'>📞</tg-emoji> Контакты:</b>\n"
            "• Вопросы, Заказы, Реклама: @llRGaming | <a href='https://vk.com/llrgaming'>VK</a>\n"
            "• Вопросы по дуэлям, боту, чату: @YaGraze\n"
            "• Предложить новость: @agent_xleb\nЛибо напишите в сообщения группы\n"
            "• По поводу разбана: @pan1q"
        )

        sent_msg = await message.reply(safe_text, reply_markup=keyboard)

        await asyncio.sleep(0.1)

        await sent_msg.edit_text(final_text, reply_markup=keyboard, disable_web_page_preview=True)

    except Exception as e:
        await log_to_owner(f"❌ Ошибка авто-коммента: {e}")

#-------------------------------------------------------------------------------------------------------------------ПРИВЕТСТВИЕ + ПРОВЕРКА
@dp.message(F.new_chat_members)
async def welcome(message: types.Message):
    for user in message.new_chat_members:
        if user.is_bot: continue

        username = user.username or user.first_name
        user_id = user.id

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="‼️ НАЖМИ НА МЕНЯ ‼️", callback_data=f"verify_{user_id}")]
        ])
        
        msg = await message.answer(
            f"<tg-emoji emoji-id='5458603043203327669'>🔔</tg-emoji> Глаза выше, Страж @{username}! \n"
            f"<tg-emoji emoji-id='5251203410396458957'>🛡</tg-emoji> Система безопасности активирована. \n"
            f"<tg-emoji emoji-id='5395444784611480792'>✏️</tg-emoji> Напиши любое сообщение или нажми кнопку ниже, чтобы подтвердить свой Свет.\n"
            f"<tg-emoji emoji-id='5260293700088511294'>🚫</tg-emoji> Иначе придется тебя изгнать в пустоту (BAN).\n\n"
            f"У тебя есть 5 минут.",
            reply_markup=kb
        )

        task = asyncio.create_task(verification_timer(message.chat.id, user_id, username, msg.message_id))

        PENDING_VERIFICATION[user_id] = {
            'task': task,
            'msg_id': msg.message_id,
            'remind_msg_id': None
        }

@dp.callback_query(F.data.startswith("verify_"))
async def verify_button_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    target_id = int(callback.data.split("_")[1])
    
    if user_id != target_id:
        await callback.answer("Это не твоя проверка!", show_alert=True)
        return

    if user_id in PENDING_VERIFICATION:
        data = PENDING_VERIFICATION[user_id]
        data['task'].cancel()
        
        try: await bot.delete_message(callback.message.chat.id, data['msg_id'])
        except: pass
        if data['remind_msg_id']:
            try: await bot.delete_message(callback.message.chat.id, data['remind_msg_id'])
            except: pass
            
        username = callback.from_user.username or callback.from_user.first_name
        success = await callback.message.answer(f"<b><tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> Допуск получен, Страж @{username}</b>. Добро пожаловать. Помни, я всё вижу.")
        asyncio.create_task(delete_later(success, 15))
        
        del PENDING_VERIFICATION[user_id]
    
    await callback.answer("Успешно!")

@dp.message()
async def moderate_and_chat(message: types.Message):
    global LAST_MESSAGE_TIME
    LAST_MESSAGE_TIME = datetime.now()
    
    if not message.text or message.from_user.id == bot.id:
        return

    text_lower = message.text.lower()
    username = message.from_user.username or message.from_user.first_name
    chat_username = message.chat.username
    user_id = message.from_user.id

    # Регистрируем чат, если это не личка
    if message.chat.type in ["group", "supergroup"]:
        register_chat(message.chat.id, message.chat.title)
    
    # --- ШПИОНСКИЙ РЕЖИМ ---
    # Если бот пишет НЕ в основном чате и НЕ в ЛС с админом
    if message.chat.id != CHAT_ID and message.chat.id != OWNER_ID:
        try:
            chat_name = message.chat.title or "ЛС"
            user_info = f"@{username}" if message.from_user.username else message.from_user.first_name
            
            # Пересылаем сообщение
            await bot.forward_message(OWNER_ID, message.chat.id, message.message_id)
            
            # Добавляем контекст
            await bot.send_message(OWNER_ID, f"📨 <b>Из чата:</b> {chat_name}\n👤 <b>От:</b> {user_info}")
        except: pass
    
    # --- ФИЛЬТР РЕПОСТОВ (АНТИ-РЕКЛАМА) ---
    if message.forward_from_chat:
        # ID твоего канала (замени на свой, можно узнать через @getmyid_bot переслав пост)
        MY_CHANNEL_ID = -1002130773598
        
        # Если это репост НЕ из нашего канала
        if message.forward_from_chat.id != MY_CHANNEL_ID:
            try:
                await message.delete()
                # Можно предупредить (опционально)
                msg = await message.answer(f"<tg-emoji emoji-id='5260293700088511294'>🚫</tg-emoji> @{username}, репосты из чужих каналов запрещены.")
                asyncio.create_task(delete_later(message, 5))
                return
            except: pass

# --- YOUTUBE / TIKTOK DOWNLOADER ---
    if "youtube.com" in message.text or "youtu.be" in message.text:
        url = extract_urls(message.text)[0]
        # Используем run_in_executor, чтобы не блокировать бота
        loop = asyncio.get_event_loop()
        video_url, title = await loop.run_in_executor(None, get_video_url, url)
        
        if video_url:
            await message.reply_video(video_url, caption=f"<tg-emoji emoji-id='5373251851074415873'>📝</tg-emoji> <b>{title}</b>")
    
    # --- ОБНОВЛЕНИЕ БАЗЫ НИКОВ ---
    if message.from_user.username:
        try:
            uid = message.from_user.id
            uname = message.from_user.username.lower()
            name = message.from_user.first_name
            # Сохраняем ник в базу
            cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (uid,))
            cursor.execute('UPDATE users SET username = ?, name = ? WHERE user_id = ?', (uname, name, uid))
            conn.commit()
        except: pass

    if message.from_user.id != bot.id:
        update_msg_stats(message.from_user.id)
    
#-------------------------------------------------------------------------------------------------------------------ТЕНЕВОЙ БАН (AMUTE)
    if message.from_user.id in SILENT_MODE_USERS:
        try:
            await message.delete()
        except: pass
        return
    
#-------------------------------------------------------------------------------------------------------------------ПРОВЕРКА НОВИЧКА
    if user_id in PENDING_VERIFICATION:
        data = PENDING_VERIFICATION[user_id]
        data['task'].cancel()

        try: await bot.delete_message(message.chat.id, data['msg_id'])
        except: pass
        if data['remind_msg_id']:
            try: await bot.delete_message(message.chat.id, data['remind_msg_id'])
            except: pass
            
        success_msg = await message.reply(f"<b><tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> Допуск получен, Страж @{username}</b>. Добро пожаловать. Помни, я всё вижу.")
        asyncio.create_task(delete_later(success_msg, 15))
        
        del PENDING_VERIFICATION[user_id]
    
#-------------------------------------------------------------------------------------------------------------------GALREIZ
    if message.from_user.username and message.from_user.username.lower() == "galreiz":
        if random.randint(1, 3) == 1:
            try:
                await message.react([ReactionTypeEmoji(emoji="🤡")])
            except Exception as e:
                await log_to_owner(f"❌ Ошибка реакции галрейз: {e}")

#-------------------------------------------------------------------------------------------------------------------РЕАКЦИЯ ДЛЯ ПОБЕДИТЕЛЯ ТУРНИРА (ВСЕГДА 🏆)
    user = message.from_user
    if (user.username and user.username.lower() == "pan1q") or user.id == 709473070: # Вставь ID
        try:
            await message.react([ReactionTypeEmoji(emoji="🏆")])
        except Exception as e:
            await log_to_owner(f"⚠️ Ошибка реакции чемпиона: {e}")
    
#-------------------------------------------------------------------------------------------------------------------БАН
    for word in BAN_WORDS:
        if word in text_lower:
            try:
                await message.delete()
                await message.chat.ban(message.from_user.id)
                msg = await message.answer(f"<tg-emoji emoji-id='5260293700088511294'>🚫</tg-emoji> @{username} улетел в бан. Воздух стал чище.")
                asyncio.create_task(delete_later(msg, 15))
                return
            except Exception as e:
                await log_to_owner(f"❌ Ошибка бана: {e}")

#-------------------------------------------------------------------------------------------------------------------УДАЛЕНИЕ
    for word in BAD_WORDS:
        if word in text_lower:
            try:
                await message.delete()
                msg = await message.answer(f"<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> <b>@{username}, рот с мылом помой</b>, у тебя скверна изо рта лезет.")
                asyncio.create_task(delete_later(msg, 15))
                return
            except Exception as e:
                await log_to_owner(f"❌ Ошибка удаления мата: {e}")

#-------------------------------------------------------------------------------------------------------------------ССЫЛКИ
    if not is_link_allowed(message.text, chat_username):
        try:
            await message.delete()
            msg = await message.answer(f"<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> <b>@{username}, ссылки на чужие помойки запрещены</b>. Не засоряй сеть Вексов.")
            asyncio.create_task(delete_later(msg, 15))
            return
        except Exception as e:
            await log_to_owner(f"❌ Ошибка удаления ссылки: {e}")

#-------------------------------------------------------------------------------------------------------------------VPN
    if "vpn" in text_lower or "впн" in text_lower:
        vpn_msg = random.choice(VPN_PHRASES)
        await message.reply(vpn_msg)
        return 

#-------------------------------------------------------------------------------------------------------------------ТАПИР
    if "тапир" in text_lower or "tapir" in text_lower:
        tapir_msg = random.choice(TAPIR_PHRASES)
        tapir_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔧 Гайд: обход тапира", url=LINK_TAPIR_GUIDE)]
        ])
        await message.reply(tapir_msg, reply_markup=tapir_kb)
        return 
        
#-------------------------------------------------------------------------------------------------------------------КЛОУН
    if message.reply_to_message and "клоун" in text_lower:
        try:
            await message.reply_to_message.react([ReactionTypeEmoji(emoji="🤡")])
        except Exception as e:
            await log_to_owner(f"❌ Ошибка реакции клоун: {e}")

#-------------------------------------------------------------------------------------------------------------------ДЕРЖИ В КУРСЕ
    if message.reply_to_message and "держи в курсе" in text_lower:
        try:
            await message.reply_to_message.reply_sticker(sticker=KEEP_POSTED_STICKER_ID)
        except Exception:
            pass
    
#-------------------------------------------------------------------------------------------------------------------РЕФАНД
    is_refund = any(word in text_lower for word in REFUND_KEYWORDS)
    if is_refund:
        try:
            await message.reply_sticker(sticker="CAACAgIAAxkBAAMWaW-qYjAAAYfnq0GFJwER5Mh-AAG7ywAC1YMAApJ_SEvZaHqj_zTQLzgE")
        except Exception as e:
            await log_to_owner(f"❌ Не могу отправить стикер. Ошибка:\n{e}")
            await message.reply(f"⚠️ Не могу отправить стикер. Ошибка:\n{e}")
        return

#-------------------------------------------------------------------------------------------------------------------ИИ (ТОЛЬКО ПО ТЕГУ + КУЛДАУН)
    bot_info = await bot.get_me()

    is_mention = f"@{bot_info.username}" in message.text

    if is_mention:
        clean_text = message.text.replace(f"@{bot_info.username}", "").strip()
        
        if not clean_text:
            msg = await message.answer("Чего звал? Пиши вопрос сразу. <tg-emoji emoji-id='5316850074255367258'>🤬</tg-emoji>")
            asyncio.create_task(delete_later(msg, 5))
            return

        global AI_COOLDOWN_TIME
        now = datetime.now()
        
        if now < AI_COOLDOWN_TIME:
            time_left = AI_COOLDOWN_TIME - now
            minutes_left = int(time_left.total_seconds() // 60) + 1
            
            msg = await message.reply(
                f"Я сейчас занят, лайт поднимаю в портале. <tg-emoji emoji-id='5319185561506816272'>😊</tg-emoji>"
                f"Обратись ко мне через <b>{minutes_left} мин</b>, когда курить пойду. <tg-emoji emoji-id='5319087606187695888'>🚬</tg-emoji>"
            )
            asyncio.create_task(delete_later(msg, 5))
            return

        try:
            await bot.send_chat_action(message.chat.id, action="typing")
            
            response = await client.chat.completions.create(
                model="sonar",
                messages=[
                    {"role": "system", "content": AI_SYSTEM_PROMPT},
                    {"role": "user", "content": clean_text}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            ai_reply = response.choices[0].message.content
            await message.reply(ai_reply)
            
            AI_COOLDOWN_TIME = datetime.now() + timedelta(minutes=5)
            
        except Exception as e:
            error_text = str(e)[:300]
            await log_to_owner(f"❌ Ошибка ИИ: {error_text}")  

    if message.text:
        chat_id = message.chat.id
    
        # Если чата нет в памяти — создаем список
        if chat_id not in CHAT_HISTORY:
            CHAT_HISTORY[chat_id] = []
        
        entry = f"{username}: {message.text[:150]}"
        CHAT_HISTORY[chat_id].append(entry)
    
        # Ограничиваем до 150 сообщений
        if len(CHAT_HISTORY[chat_id]) > 150:
            CHAT_HISTORY[chat_id].pop(0)
            
#-------------------------------------------------------------------------------------------------------------------ЗАПУСК!!!

async def main():
    print(f"Бот запущен и готов к работе.")

    print(f"Время сервера: {datetime.now()}")

    print(f"⏰ ВРЕМЯ СЕРВЕРА: {datetime.now()}")

    asyncio.create_task(check_silence_loop())

    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(send_morning_voice, "cron", hour=7, minute=00, timezone=pytz.timezone("Europe/Moscow"))

    scheduler.start()
    
    dp.message.middleware(AntiFloodMiddleware())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())







































































































