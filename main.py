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
import aiohttp
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

BUNGIE_API_KEY = "58ae872eeddb40758274693fd5a48e5c" 

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
STAT_CACHE = {} 
GAME_LOCKS = {}
ROAST_COOLDOWN = {}

ADMIN_CHAT_ID = -1003846681143
CHAT_ID = -1002129048580
DEV_CHAT_ID = -1003614362998

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
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Скиталец отстрелил тебе руку, Страж. Где твой призрак? (15 мин.)",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Вайп! @username перепутал механику и теперь сидит в муте 15 минут.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Телесто снова сломало игру... и твою возможность говорить. @username молчит 15 минут.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Ты пойман в ловушку Вексов. Связь потеряна на 15 минут."
]

MUTE_CRITICAL_PHRASES = [
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> КРИТИЧЕСКИЙ УРОН! @username словил хедшот с ульты. Молчишь 30 МИНУТ.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Вайп! Ты подвел команду. @username отправляется в мут на 30 МИНУТ.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Архитекторы решили тебя уничтожить. @username замучен чате на 30 минут.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> Громовой удар! Посиди в муте 30 минут, только без паники.",
    "<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> В твоё лицо снова прилетело. Теперь ты изуродован. (30 мин.)"
]

SAFE_PHRASES = [
    "<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> Странник избрал тебя. Живи пока.",
    "<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> У тебя что, 100 Здоровья? Пуля отскочила.",
    "<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> ЛВ выстрелил, но призрак успел тебя воскресить. Повезло.",
    "<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> Рандом на твоей стороне, Страж. ЛВ осечку дал.",
    "<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> Ты увернулся, как Хант с перекатом. Заряжаем ЛВ заново?"
]

EMB_PHRASE = [
    "<tg-emoji emoji-id='5229011542011299168'>👑</tg-emoji> <b>777! ДЖЕКПОТ!</b>\n@username, ты прокнул ультранизкий шанс на получение <b>ЭМБЛЕМЫ</b>!!!\nПоздравляем всем чатом! <tg-emoji emoji-id='5461151367559141950'>🎉</tg-emoji>\nЗа получением пиши: @llRGaming"
]

KEEP_POSTED_STICKER_ID = "CAACAgIAAxkBAAEQSpppcOtmxGDL9gH882Rg8pZrq5eXVAACXZAAAtfYYEiWmZcGWSTJ5TgE"

REFUND_KEYWORDS = ["рефанд", "refund", "refound", "возврат средств", "вернуть деньги"]

VPN_PHRASES = ["Ты имел ввиду КВН? Измени сообщение, эти 3 буквы запрещены в чате."]

BAD_WORDS = ["лгбт", "цп", "цп", "child porn", "cp", "закладки", "мефедрон", "гашиш", "купить скорость", "чурка", "хохол", "кацап", 
    "москаль", "свинособак", "черномаз", "hohol", 
    "магазин 24/7", "hydra", "kraken", "убейся", "выпей яду", "роскомнадзорнись", "мамку ебал", "зеленский", "либераха", "гейропа", "фашист"] 

BAN_WORDS = ["Пpивeт , ты в пoиcкe paбoты ? cвяжиcь  co мнoй , y меня  еcть к тeбe пpeдлoжeниe", "в пoиcкe paбoты", "заработок в интернете", "быстрый заработок", "лучший заработок", "с доходом от", "без вложений", "работа для студентов", "доход от", "нужны люди для работы", "Можно начать сразу", "Обучение бесплатно", "подработка с доходом", "работа с доходом",
    "арбитраж крипты", "мамкин инвестор", "Пoдxодит для гибкoгo гpaфика", "Oбyчeниe пpeдocтaвляeтcя", "ктo xoчeт пoдзapабoтaть", "Cвяжeмcя c кaждым", "гибкий график", "Открыта подработка", "Подойдёт даже", "Можно работать в свободное время",
    "раскрутка счета", "Требуется команда из 5 человек для интересного проекта на 2-4 часа. Оплата начинается от 8.000 руб. Пишите в личные сообщения для уточнения деталей.", "Klad MEH", "бecплaтнoe oбyчeниe"]

ALLOWED_DOMAINS = ["d2shop.ru", "youtube.com", "youtu.be", "google.com", "yandex.ru", "github.com", "x.com", "reddit.com", "t.me", "discord.com", "vk.com", "d2gunsmith.com", "light.gg", "d2foundry.gg", "destinyitemmanager.com", "bungie.net", "d2armorpicker.com", "steamcommunity.com", "store.steampowered.com"]

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
            # Пропускаем системные сообщения
            if event.new_chat_members or event.left_chat_member:
                return await handler(event, data)
            user_id = event.from_user.id
            text = event.text or event.caption

            is_media = (event.photo or event.video or event.document or event.sticker or event.animation)
            
            # Список команд-исключений (которые НЕ надо удалять)
            WHITELIST_COMMANDS = ["/lw", "/lastword", "/ластворд", "/лв", "duel", "/lw@brhlkbot", "/lastword@brhlkbot", "/ластворд@brhlkbot", "/лв@brhlkbot", "duel@brhlkbot", "/cup", "/cup@brhlkbot"]
            
            # Проверяем: начинается с /, нет медиа, и это НЕ команда из белого списка
            if text.startswith("/") and not is_media:
                is_whitelisted = any(text.lower().startswith(cmd) for cmd in WHITELIST_COMMANDS)
                
                if not is_whitelisted:
                    asyncio.create_task(delete_later(event, 60))
            
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

class SilentModeMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, types.Message):
            if event.chat.type == "private" and event.from_user.id == OWNER_ID:
                return await handler(event, data)
            user_id = event.from_user.id
            
            # Проверка
            if user_id in SILENT_MODE_USERS:
                end_time = SILENT_MODE_USERS[user_id]
                
                # Если время вышло — размучиваем
                if datetime.now() > end_time:
                    del SILENT_MODE_USERS[user_id]
                    save_silent()
                    # Можно написать "Ты свободен", но лучше не спамить
                else:
                    # Если еще в муте — удаляем и блокируем
                    try: await event.delete()
                    except: pass
                    return 
                    
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

cursor.execute('''
    CREATE TABLE IF NOT EXISTS twitter_state (
        account TEXT PRIMARY KEY,
        last_post_id TEXT
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
''')
conn.commit()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN warns INTEGER DEFAULT 0")
except: pass
conn.commit()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN warn_cycles INTEGER DEFAULT 0")
except: pass
conn.commit()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN bungie_name TEXT")
    conn.commit()
except: pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN reputation INTEGER DEFAULT 0")
    conn.commit()
except: pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN last_downvote TEXT")
except: pass
conn.commit()

#-------------------------------------------------------------------------------------------------------------------ФУНКЦИИ БД

DUELS_FILE = os.path.join(DATA_DIR, "duels.json")
TAGS_FILE = os.path.join(DATA_DIR, "tagged_users.json")
SILENT_FILE = os.path.join(DATA_DIR, "silent_users.json")

def get_rep_stats():
    """Возвращает топ-5 лучших и худших по репутации"""
    try:
        # Лучшие
        cursor.execute("SELECT user_id, name, reputation FROM users ORDER BY reputation DESC LIMIT 5")
        top_best = cursor.fetchall()
        
        # Худшие (только те, у кого < 0)
        cursor.execute("SELECT user_id, name, reputation FROM users WHERE reputation < 0 ORDER BY reputation ASC LIMIT 5")
        top_worst = cursor.fetchall()
        
        return top_best, top_worst
    except: return [], []

def check_downvote_cooldown(user_id):
    """Возвращает True, если КД прошло, иначе False"""
    try:
        cursor.execute("SELECT last_downvote FROM users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        
        if not res or not res[0]: return True # Никогда не ставил
        
        last_time = datetime.fromisoformat(res[0])
        if datetime.now() - last_time > timedelta(hours=2):
            return True
        return False
    except: return True

def update_downvote_time(user_id):
    """Обновляет время последнего минуса на сейчас"""
    try:
        now_str = datetime.now().isoformat()
        cursor.execute("UPDATE users SET last_downvote = ? WHERE user_id = ?", (now_str, user_id))
        conn.commit()
    except: pass

def remove_reputation(user_id):
    """Снимает 1 репутацию"""
    try:
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        # Не опускаем ниже 0? Или можно в минус? Давай в минус.
        cursor.execute('UPDATE users SET reputation = reputation - 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        
        cursor.execute('SELECT reputation FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()[0]
    except: return 0

def add_reputation(user_id):
    """Добавляет +1 к репутации и возвращает новое значение"""
    try:
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        cursor.execute('UPDATE users SET reputation = reputation + 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        
        cursor.execute('SELECT reputation FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()[0]
    except: return 0

def load_silent():
    if os.path.exists(SILENT_FILE):
        try:
            with open(SILENT_FILE, "r") as f:
                data = json.load(f)
                # Конвертируем строки обратно в datetime и ключи в int
                return {int(k): datetime.fromisoformat(v) for k, v in data.items()}
        except: return {}
    return {}

def save_silent():
    try:
        data = {k: v.isoformat() for k, v in SILENT_MODE_USERS.items()}
        with open(SILENT_FILE, "w") as f:
            json.dump(data, f)
    except: pass

SILENT_MODE_USERS = load_silent()

def get_setting(key):
    try:
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        res = cursor.fetchone()
        return res[0] if res else None
    except: return None

def set_setting(key, value):
    try:
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
    except: pass

def add_warn(user_id):
    """Добавляет варн и возвращает текущее количество"""
    try:
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        cursor.execute('UPDATE users SET warns = warns + 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        
        cursor.execute('SELECT warns FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()[0]
    except: return 0

def reset_warns(user_id):
    """Сбрасывает варны"""
    try:
        cursor.execute('UPDATE users SET warns = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
    except: pass

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
    """Возвращает топ-5 по сообщениям и топ-5 Рейтинга (с играми)"""
    try:
        # 1. Топ болтунов
        cursor.execute('SELECT user_id, msg_count FROM users ORDER BY msg_count DESC LIMIT 10')
        top_chatters = cursor.fetchall()

        # 2. Топ рейтинга (ID, Очки, Игры)
        cursor.execute('SELECT user_id, points, (wins + losses) as games FROM users ORDER BY points DESC LIMIT 5')
        top_rating = cursor.fetchall()

        cursor.execute('SELECT user_id, reputation FROM users ORDER BY reputation DESC LIMIT 5')
        top_rep = cursor.fetchall()
        
        return top_chatters, top_rating, top_rep
    except Exception:
        return [], []

ACTIVE_DUELS = load_duels()

async def update_manifest():
    print("⏳ Скачиваю Манифест Bungie...")
    async with aiohttp.ClientSession() as session:
        # 1. Получаем путь к файлу
        async with session.get("https://www.bungie.net/Platform/Destiny2/Manifest/", headers={"X-API-Key": BUNGIE_API_KEY}) as resp:
            data = await resp.json()
            path = data["Response"]["mobileWorldContentPaths"]["ru"] # Русский язык
            
        # 2. Скачиваем файл
        url = "https://www.bungie.net" + path
        async with session.get(url) as resp:
            with open("manifest.zip", "wb") as f:
                f.write(await resp.read())
                
    # 3. Распаковываем
    with zipfile.ZipFile("manifest.zip", 'r') as zip_ref:
        zip_ref.extractall("data")
        # Файл внутри имеет странное имя, надо переименовать в manifest.sqlite
        for name in zip_ref.namelist():
            if name.endswith(".content"):
                os.rename(os.path.join("data", name), os.path.join("data", "manifest.sqlite"))
                break
                
    print("✅ Манифест обновлен!")

def get_item_name_from_manifest(item_hash):
    """Ищет название предмета в локальной базе Manifest"""
    try:
        item_hash = int(item_hash)
        if item_hash > 2147483647: item_hash -= 4294967296
        mf_path = os.path.join(DATA_DIR, "manifest.sqlite")
        with sqlite3.connect(mf_path) as conn_mf:
            cursor_mf = conn_mf.cursor()
            cursor_mf.execute("SELECT json FROM DestinyInventoryItemDefinition WHERE id = ?", (item_hash,))
            row = cursor_mf.fetchone()
            if row:
                data = json.loads(row[0])
                return data["displayProperties"]["name"]
    except: pass
    return "Неизвестное оружие"

def get_title_name(title_hash):
    """Ищет название Титула (Печати) в Манифесте"""
    try:
        title_hash = int(title_hash)
        if title_hash > 2147483647: title_hash -= 4294967296
        mf_path = os.path.join(DATA_DIR, "manifest.sqlite")
        with sqlite3.connect(mf_path) as conn_mf:
            cursor_mf = conn_mf.cursor()
            cursor_mf.execute("SELECT json FROM DestinyRecordDefinition WHERE id = ?", (title_hash,))
            row = cursor_mf.fetchone()
            if row:
                data = json.loads(row[0])
                return data["displayProperties"]["name"]
    except: pass
    return "Нет"

async def get_clan_info(membership_type, membership_id):
    """Получает название и тег клана"""
    headers = {"X-API-Key": BUNGIE_API_KEY}
    url = f"https://www.bungie.net/Platform/GroupV2/User/{membership_type}/{membership_id}/0/1/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            try:
                group = data["Response"]["results"][0]["group"]
                return f"[{group['clanInfo']['clanCallsign']}] {group['name']}"
            except:
                return "Нет клана"

#-------------------------------------------------------------------------------------------------------------------ОБЩИЕ ФУНКЦИИ
def clean_log_text(text):
    """Удаляет HTML теги и оставляет только эмодзи из tg-emoji"""
    text = re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', text)
    
    # 2. Удаляем все остальные теги (<b>, </b>, <i>...)
    text = re.sub(r'<[^>]+>', '', text)
    
    return text
    
#-------------------------------------------------------------------------------------------------------------------ОСНОВНАЯ ФУНКЦИЯ СТАТИСТИКИ

async def get_trn_elo(bungie_name):
    """Получает ELO с DestinyTracker"""
    # Если ключа нет — возвращаем заглушку
    if not TRN_API_KEY: return "N/A", "N/A"
    
    try:
        name_enc = bungie_name.replace("#", "%23")
        url = f"https://public-api.tracker.gg/v2/destiny-2/standard/profile/bungie/{name_enc}"
        headers = {"TRN-Api-Key": TRN_API_KEY}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200: return "N/A", "N/A"
                data = await resp.json()
                
                segments = data["data"]["segments"]
                elo = 0
                
                # Ищем Trials или Comp
                for seg in segments:
                    mode = seg["metadata"]["name"]
                    if mode == "Trials of Osiris":
                        elo = seg["stats"]["elo"]["displayValue"]; break
                
                if not elo:
                    for seg in segments:
                        if seg["metadata"]["name"] == "Competitive":
                            elo = seg["stats"]["elo"]["displayValue"]; break
                            
                return elo if elo else "N/A", "N/A"
    except:
        return "N/A", "N/A"
        
async def get_full_destiny_stats(bungie_name):
    headers = {"X-API-Key": BUNGIE_API_KEY}
    
    # Проверка формата имени
    if "#" not in bungie_name:
        return "Неверный формат Bungie Name."
    name_part, code_part = bungie_name.split("#")

    # 0. СЛОВАРЬ ОРУЖИЯ
    WEAPON_MAP = {
        "HandCannon": "<tg-emoji emoji-id='5244631307274718946'>🔫</tg-emoji> Револьвер", "AutoRifle": "<tg-emoji emoji-id='5244629911410344790'>🔫</tg-emoji> Автомат", "SniperRifle": "<tg-emoji emoji-id='5244916987024408140'>🔫</tg-emoji> Снайперка",
        "Shotgun": "<tg-emoji emoji-id='5246905896184874256'>🔫</tg-emoji> Дробовик", "FusionRifle": "<tg-emoji emoji-id='5244747975766346491'>🔫</tg-emoji> Плазменка", "RocketLauncher": "<tg-emoji emoji-id='5219819319860434135'>🔫</tg-emoji> Ракетница",
        "PulseRifle": "<tg-emoji emoji-id='5244803922010347055'>🔫</tg-emoji> Пульса", "ScoutRifle": "<tg-emoji emoji-id='5244917837427934109'>🔫</tg-emoji> Скаут", "Submachinegun": "<tg-emoji emoji-id='5246884743470943062'>🔫</tg-emoji> ПП",
        "Sidearm": "<tg-emoji emoji-id='5247151357860808855'>🔫</tg-emoji> Пистолет", "Bow": "<tg-emoji emoji-id='5247013936087205519'>🔫</tg-emoji> Лук", "GrenadeLauncher": "<tg-emoji emoji-id='5247153969200923666'>🔫</tg-emoji>  Гранатомет",
        "Sword": "<tg-emoji emoji-id='5247097198323203988'>🔫</tg-emoji> Меч", "MachineGun": "<tg-emoji emoji-id='5244796491716920827'>🔫</tg-emoji> Пулемет", "Glaive": "<tg-emoji emoji-id='5247060106985636331'>🔫</tg-emoji> Глефа",
        "LinearFusionRifle": "<tg-emoji emoji-id='5217523028480529505'>🔫</tg-emoji> Линейка", "TraceRifle": "<tg-emoji emoji-id='5219739716936566996'>🔫</tg-emoji> Лучевая"
    }
    
    # --- ИНИЦИАЛИЗАЦИЯ (Защита от NameError) ---
    rank = "?"; score = "?"; comm = 0; hours = 0
    fav_class = "Не определен"; fav_class_ru = "Не определен"
    title_name = "Нет"; fav_activity_text = "Нет данных"
    kd = "0.00"; kda = "0.00"; flawless = 0; solo_dung = 0
    fav_pvp = "N/A"; fav_pve = "N/A"
    raids = 0; dungeons = 0; char_ids = []
    clan_name = "Нет клана"
    gambit_total = 0; dungeons_time = 0; raids_time = 0
    last_seen = "Неизвестно"; comp_rank = "Нет ранга"; elo_val = "N/A"

    async with aiohttp.ClientSession() as session:
        # 1. Поиск игрока
        search_url = "https://www.bungie.net/Platform/Destiny2/SearchDestinyPlayerByBungieName/All/"
        payload = {"displayName": name_part, "displayNameCode": code_part}
        async with session.post(search_url, json=payload, headers=headers) as resp:
            search_data = await resp.json()
            if not search_data.get("Response"): return "Страж не найден."
            user = search_data["Response"][0]
            mem_id, mem_type = user["membershipId"], user["membershipType"]

        # 1.1 Клан
        clan_url = f"https://www.bungie.net/Platform/GroupV2/User/{mem_type}/{mem_id}/0/1/"
        async with session.get(clan_url, headers=headers) as resp:
            try:
                c_data = await resp.json()
                if c_data.get("Response") and c_data["Response"]["results"]:
                    group = c_data["Response"]["results"][0]["group"]
                    clan_name = f"[{group['clanInfo']['clanCallsign']}] {group['name']}"
            except: pass

        # 2. Профиль
        profile_url = f"https://www.bungie.net/Platform/Destiny2/{mem_type}/Profile/{mem_id}/?components=100,200,900,1100,1400,202,205"
        async with session.get(profile_url, headers=headers) as resp:
            p_data = await resp.json()
            if "Response" not in p_data: return "Профиль скрыт настройками приватности."
            p = p_data["Response"]

            # --- ВЫЧИСЛЯЕМ МЕЙНА И ВРЕМЯ ---
            chars = p["characters"]["data"]
            char_ids = list(chars.keys())
            total_minutes = 0
            class_map = {"0": "Titan", "1": "Hunter", "2": "Warlock"}
            class_counts = {"Titan": 0, "Hunter": 0, "Warlock": 0}
            max_mins = -1
            fav_char_id = None

            for cid, c_info in chars.items():
                m = int(c_info.get("minutesPlayedTotal", 0))
                total_minutes += m
                if m > max_mins:
                    max_mins = m
                    fav_char_id = cid
                c_name = class_map.get(str(c_info["classType"]), "Unknown")
                if c_name in class_counts: class_counts[c_name] += m
            
            hours = total_minutes // 60
            if class_counts: fav_class = max(class_counts, key=class_counts.get)
            else: fav_class = "Warlock"

            ru_classes = {"Hunter": "<tg-emoji emoji-id='5244683538372003160'>🥷</tg-emoji> Охотник", "Warlock": "<tg-emoji emoji-id='5247141865983081163'>🧙‍♂️</tg-emoji> Варлок", "Titan": "<tg-emoji emoji-id='5244864279185752756'>🛡</tg-emoji> Титан"}
            fav_class_ru = ru_classes.get(fav_class, fav_class)

            # Титул
            if fav_char_id:
                t_hash = chars[fav_char_id].get("titleRecordHash")
                if t_hash: title_name = get_title_name(t_hash)

            # --- PVP ДИВИЗИОН ---
            try:
                rank_names = [
                    "Медь III", "Медь II", "Медь I", "Бронза III", "Бронза II", "Бронза I",
                    "Серебро III", "Серебро II", "Серебро I", "Золото III", "Золото II", "Золото I",
                    "Платина III", "Платина II", "Платина I", "Адепт III", "Адепт II", "Адепт I",
                    "Вознесшийся III", "Вознесшийся II", "Вознесшийся I"
                ]
                
                # Сначала ищем в персонаже
                char_progressions = p.get("characterProgressions", {}).get("data", {}).get(fav_char_id, {}).get("progressions", {})
                comp_data = char_progressions.get("3696598664")
                
                if comp_data:
                    step = comp_data.get("stepIndex", 0)
                    if comp_data.get("currentProgress", 0) > 0 or step > 0:
                        comp_rank = rank_names[step] if step < len(rank_names) else "Вознесшийся I"
                    else:
                        comp_rank = "Не откалиброван"
                
                # Если не нашли, ищем в профиле (Fallback)
                if comp_rank == "Нет ранга":
                    prof_progress = p.get("profileProgression", {}).get("data", {}).get("progressions", {})
                    if "3696598664" in prof_progress:
                        step = prof_progress["3696598664"].get("stepIndex", 0)
                        comp_rank = rank_names[step] if step < len(rank_names) else "Вознесшийся I"
            except: pass

            # Ранг, Очки, Слава
            try: rank = p["profile"]["data"].get("currentGuardianRank", "?")
            except: pass
            try: score = p["profileRecords"]["data"].get("activeScore", "?")
            except: pass
            try: comm = p.get("profileCommendations", {}).get("data", {}).get("totalScore", 0)
            except: pass

            # Метрики
            m_list = p.get("metrics", {}).get("data", {}).get("metrics", {})
            try: flawless = m_list.get("1765255052", {}).get("objectiveProgress", {}).get("progress", 0)
            except: pass
            try: solo_dung = m_list.get("307982000", {}).get("objectiveProgress", {}).get("progress", 0)
            except: pass

            # Последний вход
            last_seen_str = p["profile"]["data"].get("dateLastPlayed", "")
            try:
                dt = datetime.fromisoformat(last_seen_str.replace("Z", "+00:00"))
                last_seen = dt.strftime("%d.%m.%Y")
            except: pass

        # 3. Общая статистика (ИСПРАВЛЕННЫЙ БЛОК)
        stats_url = f"https://www.bungie.net/Platform/Destiny2/{mem_type}/Account/{mem_id}/Stats/"
        async with session.get(stats_url, headers=headers) as resp:
            s_data = await resp.json()
            
            # Функция поиска оружия
            def find_fav_weapon(data_node):
                if not data_node: return "N/A"
                bw = "N/A"; mk = 0
                for k, v in data_node.items():
                    if "weaponKills" in k:
                        wt = k.replace("weaponKills", "")
                        if wt in ["Super", "Melee", "Grenade", "Relic"]: continue
                        try:
                            kills = int(v["basic"]["value"])
                            if kills > mk:
                                mk = kills; 
                                ru_n = WEAPON_MAP.get(wt, wt)
                                bw = f"{ru_n} ({kills})"
                        except: continue
                return bw

            # ПРОВЕРКА НАЛИЧИЯ СТАТИСТИКИ (Чтобы не было KeyError)
            if "Response" in s_data and s_data["Response"].get("mergedAllCharacters"):
                res = s_data["Response"]["mergedAllCharacters"]["results"]
                
                # Безопасный доступ к PvP
                all_pvp = res.get("allPvP", {}).get("allTime")
                if all_pvp:
                    try:
                        kd = all_pvp["killsDeathsRatio"]["basic"]["displayValue"]
                        kda = all_pvp["killsDeathsAssists"]["basic"]["displayValue"]
                    except: pass
                    fav_pvp = find_fav_weapon(all_pvp)
                
                # Безопасный доступ к PvE
                all_pve = res.get("allPvE", {}).get("allTime")
                if all_pve:
                    fav_pve = find_fav_weapon(all_pve)

                # Любимая активность
                modes = ["allPvE", "allPvP", "allPvECompetitive", "raid", "dungeon"]
                m_counts = {}
                for m in modes:
                    try: 
                        val = res.get(m, {}).get("allTime", {}).get("activitiesEntered", {}).get("basic", {}).get("value", 0)
                        m_counts[m] = int(val)
                    except: m_counts[m] = 0
                
                if m_counts:
                    top_m = max(m_counts, key=m_counts.get)
                    ru_m = {"allPvE": "PvE", "allPvP": "Горнило", "allPvECompetitive": "Гамбит", "raid": "Рейды", "dungeon": "Подземелья"}
                    cnt = m_counts[top_m]
                    if cnt > 0: fav_activity_text = f"{ru_m.get(top_m, top_m)} ({cnt} раз)"
                    else: fav_activity_text = "Нет активности"
            else:
                fav_activity_text = "Скрыто/Нет данных"

        # 4. Детальная статистика (Рейды, Гамбит)
        for cid in char_ids:
            url_c = f"https://www.bungie.net/Platform/Destiny2/{mem_type}/Account/{mem_id}/Character/{cid}/Stats/?modes=4,82,63"
            async with session.get(url_c, headers=headers) as resp:
                try:
                    c_res = await resp.json()
                    if "Response" in c_res:
                        r_data = c_res["Response"]
                        # Гамбит
                        if "gambit" in r_data and "allTime" in r_data["gambit"]:
                            gambit_total += int(r_data["gambit"]["allTime"]["activitiesEntered"]["basic"]["value"])
                        # Рейды
                        if "raid" in r_data and "allTime" in r_data["raid"]:
                            raids += int(r_data["raid"]["allTime"]["activitiesCleared"]["basic"]["value"])
                            raids_time += int(r_data["raid"]["allTime"]["secondsPlayed"]["basic"]["value"])
                        # Данжи
                        if "dungeon" in r_data and "allTime" in r_data["dungeon"]:
                            dungeons += int(r_data["dungeon"]["allTime"]["activitiesCleared"]["basic"]["value"])
                            dungeons_time += int(r_data["dungeon"]["allTime"]["secondsPlayed"]["basic"]["value"])
                except: pass

        # 5. ELO
        try: elo_val, _ = await get_trn_elo(bungie_name)
        except: pass
    
    return {
        "name": bungie_name, "class_ru": fav_class_ru, "title": title_name, "clan": clan_name, "comp_rank": comp_rank,
        "rank": rank, "score": score, "comm": comm, "hours": hours, "clan": clan_name, "elo": elo_val,
        "gambit": gambit_total, "last_seen": last_seen,"raid_hours": raids_time // 3600,
        "dungeon_hours": dungeons_time // 3600,
        "kd": kd, "kda": kda, "flawless": flawless, "fav_pvp": fav_pvp, "fav_activity_text": fav_activity_text,
        "raids": int(raids), "dungeons": int(dungeons), "solo_dung": solo_dung, "fav_class_ru": fav_class_ru, "fav_pve": fav_pve
    }

async def check_donate_post():
    try:
        next_post_str = get_setting("next_donate_post")
        now = datetime.now()
        
        if not next_post_str: next_post = now
        else: next_post = datetime.fromisoformat(next_post_str)
            
        if now >= next_post:
            # 1. Удаляем старое сообщение (если есть)
            last_msg_id = get_setting("last_donate_msg_id")
            if last_msg_id:
                try: await bot.delete_message(CHAT_ID, int(last_msg_id))
                except: pass

            # 2. Отправляем новое
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💸 Поддержать нас", url="https://pay.cloudtips.ru/p/bb9b6a35")]
            ])
            
            text = (
                "<tg-emoji emoji-id='5312138559556164615'>❤️</tg-emoji> <b>Группе нужна ваша поддержка!</b>\n\n"
                "Кто захочет поблагодарить за новости, бота, приветы от актеров озвучки, розыгрыши — Поддержать можно тут:"
            )
            
            msg = await bot.send_message(CHAT_ID, text, reply_markup=kb)
            
            # 3. Сохраняем ID нового и время
            set_setting("last_donate_msg_id", msg.message_id)
            set_setting("next_donate_post", (now + timedelta(hours=2)).isoformat())
            
    except Exception as e:
        await log_to_owner(f"❌ Ошибка донат-поста: {e}")

def load_tagged():
    if os.path.exists(TAGS_FILE):
        try:
            with open(TAGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # JSON хранит ключи как строки, конвертируем в int
                # А время храним как timestamp или строку
                parsed = {}
                for k, v in data.items():
                    # Конвертируем строку времени обратно в datetime
                    v["until"] = datetime.fromisoformat(v["until"])
                    parsed[int(k)] = v
                return parsed
        except: return {}
    return {}

def save_tagged():
    try:
        data_to_save = {}
        for k, v in TAGGED_USERS.items():
            # Конвертируем datetime в строку для JSON
            val_copy = v.copy()
            val_copy["until"] = val_copy["until"].isoformat()
            data_to_save[k] = val_copy
            
        with open(TAGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4)
    except: pass

TAGGED_USERS = load_tagged()

async def check_tagged_users():
    while True:
        try:
            await asyncio.sleep(60) # Проверка раз в минуту
        
            now = datetime.now()
            to_remove = []
        
            for uid, data in TAGGED_USERS.items():
                if now > data["until"]:
                    to_remove.append(uid)
                
                    try:
                        # Снимаем титул и права
                        await bot.set_chat_administrator_custom_title(CHAT_ID, uid, "Страж")
                        await bot.promote_chat_member(CHAT_ID, uid, can_manage_chat=False)
                    except Exception as e:
                        print(f"Ошибка снятия титула {uid}: {e}")
        except Exception as e: # <--- ДОБАВЛЕНО
            print(f"Ошибка в цикле check_tagged_users: {e}")
            await asyncio.sleep(10)

        # Удаляем из словаря
        if to_remove:
            for uid in to_remove:
                del TAGGED_USERS[uid]
            save_tagged()
        
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
        try:
            await asyncio.sleep(60) 

            await check_donate_post()
        
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
        except Exception as e: # <--- ДОБАВЛЕНО
            print(f"Ошибка в цикле silence_loop: {e}")
            await asyncio.sleep(10)

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

async def show_stat_page(message, page):
    data = STAT_CACHE.get(message.message_id)
    if not data: return
    d = message.from_user
    du = f"@{d.username}"
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    user_id = target.id # <--- СОЗДАЕМ ТУТ
    name = target.first_name
    cursor.execute("SELECT bungie_name FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    bungie_id = res[0] if res and res[0] else "Не привязан"
    text = ""
    if page == 1: # ОБЩЕЕ
        text = (
            f"<tg-emoji emoji-id='5434144690511290129'>📰</tg-emoji> <b>ДОСЬЕ: {data['name']}</b> (1/3)\n\n"
            f"<tg-emoji emoji-id='5242478394788056819'>🏆</tg-emoji> <b>Bungie:</b> <code>{bungie_id}</code>\n"
            f"<tg-emoji emoji-id='5357107601584693888'>👑</tg-emoji> <b>Ранг:</b> {data['rank']}\n"
            f"<tg-emoji emoji-id='5445267414562389170'>🗑</tg-emoji> <b>Время:</b> {data['hours']} ч.\n"
            f"<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> <b>Клан:</b> {data['clan']}\n"
            f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>Триумф:</b> {data['score']}\n"
            f"<tg-emoji emoji-id='5312138559556164615'>❤️</tg-emoji> <b>Класс:</b> {data['fav_class_ru']}\n"
            f"<tg-emoji emoji-id='5312138559556164615'>❤️</tg-emoji> <b>Активность:</b> {data['fav_activity_text']}\n"
            f"<tg-emoji emoji-id='5413879192267805083'>🗓</tg-emoji> <b>Был в игре:</b> {data['last_seen']}\n"
        )
    elif page == 2: # PVE
        text = (
            f"<tg-emoji emoji-id='5434144690511290129'>📰</tg-emoji> <b>PvE СТАТИСТИКА {data['name']}</b> (2/3)\n\n"
            f"<tg-emoji emoji-id='5244515132704326856'>💀</tg-emoji> <b>Рейдов:</b> {data['raids']}\n"
            f"<tg-emoji emoji-id='5260668302841121405'>❤️</tg-emoji> <b>Подземелий:</b> {data['dungeons']}\n"
            f"<tg-emoji emoji-id='5312138559556164615'>❤️</tg-emoji> <b>Оружие:</b> {data['fav_pve']}\n"
        )
    elif page == 3: # PVP
        text = (
            f"<tg-emoji emoji-id='5434144690511290129'>📰</tg-emoji> <b>PvP СТАТИСТИКА</b> (3/3)\n\n"
            f"<tg-emoji emoji-id='5244837092042750681'>📈</tg-emoji> <b>K/D:</b> {data['kd']}\n"
            f"<tg-emoji emoji-id='5244837092042750681'>📈</tg-emoji> <b>KDA:</b> {data['kda']}\n"
            f"<tg-emoji emoji-id='5247080598274606834'>⚔️</tg-emoji> <b>Осирис (Flawless):</b> {data['flawless']}\n"
            f"<tg-emoji emoji-id='5312138559556164615'>❤️</tg-emoji> <b>Оружие:</b> {data['fav_pvp']}"
        )
    # СТРАНИЦА 4 (ДУЭЛИ)
    elif page == 4:
        # Считаем любимое оружие/класс из локальной базы
        # (Код копируем из старой stats_command)
        wins = data.get('wins') or 0; losses = data.get('losses') or 0; pts = data.get('points') or 0
        total = wins + losses
        wr = round((wins / total) * 100, 1) if total > 0 else 0
        rank, next_pts = get_rank_info(pts)
        next_str = f"<tg-emoji emoji-id='5416117059207572332'>➡️</tg-emoji> <b>До повышения:</b> {next_pts}" if next_pts > 0 else "<tg-emoji emoji-id='5357107601584693888'>👑</tg-emoji> Максимальный ранг"
        
        # Любимое (локальное)
        classes = {"<tg-emoji emoji-id='5330515960111583947'>🐍</tg-emoji> Хантер": data.get('class_hunter') or 0, "<tg-emoji emoji-id='5330564987163267533'>🦅</tg-emoji> Варлок": data.get('class_warlock') or 0, "<tg-emoji emoji-id='5330353116426551101'>🦁</tg-emoji> Титан": data.get('class_titan') or 0}
        f_class = max(classes, key=classes.get) if sum(classes.values()) > 0 else "Не определен"
        
        weps = {
            "<tg-emoji emoji-id='5244894167863166109'>🃏</tg-emoji> Пиковый Туз": data.get('w_ace') or 0, "<tg-emoji emoji-id='5472003139303409777'>🤠</tg-emoji> Ластворд": data.get('w_lw') or 0, "<tg-emoji emoji-id='5199852661146422050'>🧪</tg-emoji> Шип": data.get('w_thorn') or 0,
            "<tg-emoji emoji-id='5471959145953396609'>🔥</tg-emoji> Золотой пистолет": data.get('w_gg') or 0, "<tg-emoji emoji-id='5469821755478547431'>🔮</tg-emoji> Нова": data.get('w_nova') or 0, "<tg-emoji emoji-id='5472214494644045946'>⚡️</tg-emoji> Громовой удар": data.get('w_crash') or 0
        }
        f_wep = max(weps, key=weps.get) if sum(weps.values()) > 0 else "Не определен"
        text = (
            f"<tg-emoji emoji-id='5434144690511290129'>📰</tg-emoji> <b>ДОСЬЕ (ДУЭЛИ): {data['name']}</b>\n\n"
            f"<tg-emoji emoji-id='5238027455754680851'>🎖</tg-emoji> <b>Ранг:</b> {rank} ({pts})\n{next_str}\n"
            f"<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> <b>Матчей:</b> {total} (WR {wr}%)\n"
            f"<tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> <b>Побед:</b> {wins}\n"
            f"❌ <b>Поражений:</b> {losses}\n"
            f"<tg-emoji emoji-id='5312138559556164615'>❤️</tg-emoji> <b>Класс:</b> {f_class}\n"
            f"<tg-emoji emoji-id='5312138559556164615'>❤️</tg-emoji> <b>Оружие:</b> {f_wep}"
        )

    # КНОПКИ
    uid = data.get("user_id")
    buttons = []
    row = []

    if page > 1 and page < 4:
        row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"stat_page:{page-1}:{uid}"))
    if page < 3:
        row.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"stat_page:{page+1}:{uid}"))
    
    if row:
        buttons.append(row)
    
    # Кнопка быстрого перехода
    if page == 4:
        buttons.append([InlineKeyboardButton(text="📊 Статы Банжи", callback_data=f"stat_page:1:{uid}")])
    else:
        buttons.append([InlineKeyboardButton(text="⚔️ Статы Дуэлей", callback_data=f"stat_page:4:{uid}")])

    try:
        await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except: pass

@dp.callback_query(F.data.startswith("stat_page:"))
async def stat_page_handler(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    page = int(parts[1])
    owner_id = int(parts[2])
    
    if callback.from_user.id != owner_id:
        await callback.answer("Не твоя статистика! Вызови свою.", show_alert=True)
        return

    await show_stat_page(callback.message, page)
    await callback.answer()

#-------------------------------------------------------------------------------------------------------------------ХЕНДЛЕРЫ

#-------------------------------------------------------------------------------------------------------------------ВЕРДИКТ ШАКСА (ROAST)
@dp.message(Command("roast"))
async def roast_command(message: types.Message):
    user_id = message.from_user.id
    now = datetime.now()

    # 1. ПРОВЕРКА КУЛДАУНА (5 МИНУТ)
    if user_id in ROAST_COOLDOWN:
        if now < ROAST_COOLDOWN[user_id]:
            time_left = ROAST_COOLDOWN[user_id] - now
            minutes_left = int(time_left.total_seconds() // 60) + 1
            seconds_left = int(time_left.total_seconds() % 60)
            
            msg = await message.reply(
                f"<tg-emoji emoji-id='5364240670384999558'>😡</tg-emoji> Не трать мое время, Страж. Приходи за новой порцией прожарки через <b>{minutes_left} мин. {seconds_left} сек.</b>"
            )
            asyncio.create_task(delete_later(msg, 10))
            asyncio.create_task(delete_later(message, 5))
            return

    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        target = message.from_user

    wait_msg = await message.reply("<i><tg-emoji emoji-id='5467539229468793355'>📞</tg-emoji> Звоню Шаксу...</i>")
    
    # --- СБОР ДАННЫХ ---
    cursor.execute("SELECT bungie_name FROM users WHERE user_id = ?", (target.id,))
    res = cursor.fetchone()
    bungie_info = "Юзер не привязал ник через команду /mybname (посмейся над этим, он даже этого не сделал)."
    
    if res and res[0]:
        stats = await get_full_destiny_stats(res[0])
        if isinstance(stats, dict):
            bungie_info = (
                f"Ник: {stats.get('name')}\n"
                f"K/D: {stats.get('kd', '0.0')}\n"
                f"Любимое оружие: {stats.get('fav_pvp', 'Нет данных')}\n"
                f"Рейдов: {stats.get('raids', 0)}\n"
                f"Flawless (Осирис): {stats.get('flawless', 0)}"
            )

    local_data = get_user_data(target.id)
    wins = local_data.get('wins', 0)
    losses = local_data.get('losses', 0)
    total = wins + losses
    winrate = round((wins / total) * 100, 1) if total > 0 else 0
    rank_title, _ = get_rank_info(local_data.get('points', 0))

    classes = {"Хантер": local_data.get('class_hunter', 0), "Варлок": local_data.get('class_warlock', 0), "Титан": local_data.get('class_titan', 0)}
    fav_class = max(classes, key=classes.get) if sum(classes.values()) > 0 else "Нет"
    weapons = {"Ace": local_data.get('w_ace', 0), "Last Word": local_data.get('w_lw', 0), "Thorn": local_data.get('w_thorns', 0), "Crash": local_data.get('w_crash', 0)}
    fav_wep = max(weapons, key=weapons.get) if sum(weapons.values()) > 0 else "Нет"

    chat_info = (
        f"Ранг в чате: {rank_title}\n"
        f"Дуэлей: {total} (Винрейт {winrate}%)\n"
        f"Любимый класс (чат): {fav_class}\n"
        f"Любимое оружие (чат): {fav_wep}"
    )

    # 3. НОВЫЙ ПРОМПТ
    system_prompt = (
        "Ты — Лорд Шакс из Destiny 2. Громкий, эмоциональный, токсичный, но справедливый комментатор Горнила. "
        "Твоя задача — 'прожарить' (roast) игрока. "
        "ПРАВИЛА ОТВЕТА:\n"
        "1. НИКАКОГО MARKDOWN (звездочек **text**). Пиши чистым текстом или иногда используй КАПС для крика, но не делай весь текст капсом.\n"
        "2. НИКАКИХ ССЫЛОК НА ИСТОЧНИКИ [1][2]. Убери их полностью.\n"
        "3. Используй реальный игровой сленг, не выдумывай свои слова, оскорбляй в стиле Destiny.\n"
        "4. Сравнивай его успехи в реальной игре и в текстовом чате. Если в чате он круче, чем в игре — назови его 'клавиатурным воином'.\n"
        "5. Будь краток и резок."
    )

    user_content = (
        f"Вот досье игрока:\n\n"
        f"--- DESTINY 2 (РЕАЛЬНОСТЬ) ---\n{bungie_info}\n\n"
        f"--- ЧАТ БАРАХОЛКИ (ТЕКСТОВЫЕ ДУЭЛИ) ---\n{chat_info}\n\n"
        "Уничтожь его словами."
    )

    try:
        response = await client.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.9 # Повысили креативность
        )
        roast_text = response.choices[0].message.content
        
        # Чистим мусор, если ИИ всё же накосячил
        roast_text = roast_text.replace("**", "").replace("[1]", "").replace("[2]", "").replace("[3]", "").replace("[4]", "")
        
        ROAST_COOLDOWN[user_id] = now + timedelta(minutes=5)
        
        await wait_msg.edit_text(f"<b><tg-emoji emoji-id='5395444784611480792'>✏️</tg-emoji> ВЕРДИКТ ШАКСА:</b>\n\n{roast_text}")
    except Exception as e:
        await log_to_owner(f"Ошибка AI Roast: {e}")
        await wait_msg.edit_text("Шакс подавился гранатой. Попробуй позже (ошибка API).")
        
@dp.message(Command("rep"))
async def rep_stats_command(message: types.Message):
    best, worst = get_rep_stats()
    
    text = "<tg-emoji emoji-id='5325547803936572038'>✨</tg-emoji> <b>ДОСКА РЕПУТАЦИИ</b>\n\n"
    
    text += "<tg-emoji emoji-id='5244837092042750681'>📈</tg-emoji> <b>Лучшие:</b>\n"
    for uid, name, rep in best:
        text += f"• <a href='tg://user?id={uid}'>{name}</a>: <b>{rep}</b>\n"
        
    text += "\n<tg-emoji emoji-id='5246762912428603768'>📉</tg-emoji> <b>Худшие:</b>\n"
    if worst:
        for uid, name, rep in worst:
            text += f"• <a href='tg://user?id={uid}'>{name}</a>: <b>{rep}</b>\n"
    else:
        text += "Пока никого. Все молодцы."
        
    msg = await message.reply(text)
    asyncio.create_task(delete_later(msg, 300))
    asyncio.create_task(delete_later(message, 5))
    
# --- РУЧНАЯ ВЫДАЧА ТИТУЛА (/adm) ---
@dp.message(Command("adm"))
async def adm_command(message: types.Message, command: CommandObject):
    if message.from_user.id != OWNER_ID: return

    if not message.reply_to_message:
        msg = await message.answer("<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> Ответь на сообщение того, кого хочешь наградить.")
        asyncio.create_task(delete_later(msg, 5)); return

    target = message.reply_to_message.from_user
    title = command.args or "Позорник" # Если титул не указан

    try:
        # Выдаем админку (Только Add Users)
        await bot.promote_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            can_invite_users=True, # Право добавлять участников
            is_anonymous=False
        )
        # Ставим титул
        await bot.set_chat_administrator_custom_title(message.chat.id, target.id, title)
        
        # Записываем в базу (чтобы снялось через час)
        TAGGED_USERS[target.id] = {
            "emoji": "🤡", # Эмодзи по умолчанию
            "until": datetime.now() + timedelta(hours=1)
        }
        save_tagged()
        
        await message.answer(f"<tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> <b>{target.first_name}</b> получил титул <b>{title}</b> на 1 час.")
        
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

# --- СНЯТИЕ ТИТУЛА (/unadm) ---
@dp.message(Command("unadm"))
async def unadm_command(message: types.Message):
    if message.from_user.id != OWNER_ID: return

    if not message.reply_to_message: return
    target = message.reply_to_message.from_user

    try:
        # Снимаем титул и права
        await bot.set_chat_administrator_custom_title(message.chat.id, target.id, "Страж")
        await bot.promote_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            can_invite_users=False,
            is_anonymous=False
        )
        
        # Удаляем из базы
        if target.id in TAGGED_USERS:
            del TAGGED_USERS[target.id]
            save_tagged()
            
        await message.answer(f"<tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> с <b>{target.first_name}</b> сняты все почести.")
        
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command("mybname"))
async def set_bungie_name_command(message: types.Message, command: CommandObject):
    name = command.args
    if not name or "#" not in name:
        msg = await message.reply("Укажи свой Bungie Name. Пример: `/mybname Name#1234`")
        asyncio.create_task(delete_later(msg, 15))
        return

    try:
        # Проверяем, существует ли такой игрок (чтобы не сохранять мусор)
        res = await get_full_destiny_stats(name)
        if isinstance(res, str): # Ошибка ("Страж не найден")
            msg = await message.reply(f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> {res}")
            asyncio.create_task(delete_later(message, 10))
            return

        # Сохраняем в БД
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
        cursor.execute("UPDATE users SET bungie_name = ? WHERE user_id = ?", (name, message.from_user.id))
        conn.commit()
        
        msg = await message.reply(f"<tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> Bungie Name <b>{name}</b> привязан! Теперь пиши просто `/stats`.")
        asyncio.create_task(delete_later(message, 60))
    except Exception as e:
        await log_to_owner(f"Ошибка mybname: {e}")

@dp.message(Command("st", "stats", "d2stat", "d2stats"))
async def unified_stat_command(message: types.Message, command: CommandObject):
    bungie_name = command.args
    user_id = message.from_user.id
    
    # 1. Если аргумента нет, ищем в базе
    if not bungie_name:
        cursor.execute("SELECT bungie_name FROM users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        if res and res[0]:
            bungie_name = res[0]
        else:
            msg = await message.reply("<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> Ты не привязал Bungie Name. `/mybname Name#1234`")
            asyncio.create_task(delete_later(msg, 15))
            return

    msg = await message.reply("<i><tg-emoji emoji-id='5467539229468793355'>📞</tg-emoji> Звоню в Bungie...</i>")
    asyncio.create_task(delete_later(msg, 200))
    try:
        # 2. Грузим Bungie (Долго)
        data = await get_full_destiny_stats(bungie_name)
        if isinstance(data, str):
            await msg.edit_text(f"<tg-emoji emoji-id='5436113877181941026'>❓</tg-emoji> {data}")
            return
            
        # 3. Грузим Дуэли (Быстро)
        local_data = get_user_data(user_id)
        # Объединяем словари
        data.update(local_data) # Теперь в data есть и Bungie, и wins/losses
        data["user_id"] = user_id # Для проверки кнопок
        
        # 4. Сохраняем и показываем
        STAT_CACHE[msg.message_id] = data
        await show_stat_page(msg, 1) # Страница 1 (Общее)
        
    except Exception as e:
        await msg.edit_text(f"Ошибка: {e}")

@dp.message(Command("stat"))
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

#-------------------------------------------------------------------------------------------------------------------ПРИВЕТСТВИЕ В ЛС (/start)
@dp.message(Command("start"))
async def start_command(message: types.Message):
    if message.chat.type != "private":
        return

    try:
        user = message.from_user
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user.id,))
        if user.username:
            cursor.execute('UPDATE users SET username = ?, name = ? WHERE user_id = ?', (user.username.lower(), user.first_name, user.id))
        conn.commit()
    except: pass

    # Клавиатура
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Гайд по боту", url=BOT_GUIDE)],
        [InlineKeyboardButton(text="♥️ Поддержать разработчиков", url="https://pay.cloudtips.ru/p/8f3e39da")]
    ])

    text = (
        f"Привет, Страж <b>{message.from_user.first_name}</b>! <tg-emoji emoji-id='5217822164362739968'>👑</tg-emoji>\n\n"
        "Я — ИИ-помощник Барахолки. Слежу за порядком, провожу дуэли и помогаю Стражам.\n\n"
        "<b>Мои возможности:</b>\n"
        "<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> <b>Дуэли:</b> `/duel` (в чате)\n"
        "<tg-emoji emoji-id='5244837092042750681'>📈</tg-emoji> <b>Статистика:</b> `/stats`\n"
        "<tg-emoji emoji-id='5325547803936572038'>✨</tg-emoji> <b>ИИ:</b> Просто тегни меня в чате\n"
        "<tg-emoji emoji-id='5276032951342088188'>💥</tg-emoji> <b>Рулетка:</b> `/lw`\n"
        "<tg-emoji emoji-id='5274099962655816924'>❗️</tg-emoji> <b>Система тэгов:</b> `/tag название`\n"
        "<b>А также много чего, подробнее <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji></b>\n\n"
        "Можешь поддержать мою работу чеканной монетой по второй кнопке снизу <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>"
    )

    await message.answer(text, reply_markup=kb)

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
    top_chatters, top_rating, top_rep = get_top_users()
    
    text = "<tg-emoji emoji-id='5350305691942788490'>📈</tg-emoji> <b>СТАТИСТИКА ЧАТА</b>\n\n"
    
    text += "<tg-emoji emoji-id='5417915203100613993'>💬</tg-emoji> <b>Болтуны чата:</b>\n"
    for i, (uid, count) in enumerate(top_chatters):
        try:
            member = await bot.get_chat_member(message.chat.id, uid)
            name = member.user.first_name
        except:
            cursor.execute("SELECT name FROM users WHERE user_id = ?", (uid,))
            res = cursor.fetchone()
            name = res[0] if res and res[0] else "Страж"
        text += f"{i+1}. {name} — {count} сообщ.\n"
        
    text += "\n<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>Лучшие дуэлянты:</b>\n"
    for i, (uid, pts, games) in enumerate(top_rating):
        try:
            member = await bot.get_chat_member(message.chat.id, uid)
            name = member.user.first_name
        except:
            cursor.execute("SELECT name FROM users WHERE user_id = ?", (uid,))
            res = cursor.fetchone()
            name = res[0] if res and res[0] else "Страж"
        
        # Получаем ранг для красоты
        rank_name, _ = get_rank_info(pts)
        
        text += f"{i+1}. {name} — {pts} очков ({games} игр)\n"

    text += "\n<tg-emoji emoji-id='5357080225463149588'>🤝</tg-emoji> <b>Топ рейтинга репутации:</b>\n"
    for i, (uid, rep) in enumerate(top_rep):
        try:
            member = await bot.get_chat_member(message.chat.id, uid)
            name = member.user.first_name
        except:
            cursor.execute("SELECT name FROM users WHERE user_id = ?", (uid,))
            res = cursor.fetchone()
            name = res[0] if res else "Страж"
        text += f"{i+1}. {name} — {rep} <tg-emoji emoji-id='5325547803936572038'>✨</tg-emoji>\n"
        
    await message.reply(text)
    asyncio.create_task(delete_later(message, 5))

#-------------------------------------------------------------------------------------------------------------------ВЫЗОВ (ПИНГ)
@dp.message(Command("newtag"))
async def new_tag_command(message: types.Message, command: CommandObject):
    # Проверка на админа
    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    is_real_admin = False
    if user_status.status == "creator":
        is_real_admin = True
    elif user_status.status == "administrator" and user_status.can_restrict_members:
        is_real_admin = True

    if not is_real_admin:
    # (Опционально) await message.reply("У тебя нет прав банить.")
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
        tags_list = ", ".join([f"{r[0]}" for r in rows])
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
        cursor.execute("SELECT tag_name FROM allowed_tags")
        rows = cursor.fetchall()
        tags_list = ", ".join([f"{r[0]}" for r in rows])
        msg = await message.reply(f"Кого звать?\nДоступные теги:\n{tags_list}\n\nПиши '/call название'")
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

#-------------------------------------------------------------------------------------------------------------------ВАРНЫ
@dp.message(Command("warn"))
async def warn_command(message: types.Message):
    # 1. Удаляем команду админа
    try: await message.delete()
    except: pass

    # 2. Проверка прав
    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    is_real_admin = False
    if user_status.status == "creator":
        is_real_admin = True
    elif user_status.status == "administrator" and user_status.can_restrict_members:
        is_real_admin = True

    if not is_real_admin:
    # (Опционально) await message.reply("У тебя нет прав банить.")
        return

    if not message.reply_to_message:
        msg = await message.answer("<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Ответь на сообщение нарушителя.")
        asyncio.create_task(delete_later(msg, 5))
        return

    target = message.reply_to_message.from_user
    target_id = target.id
    name = target.first_name

    # Нельзя варнить админов
    target_status = await bot.get_chat_member(message.chat.id, target_id)
    if target_status.status in ["administrator", "creator"]:
        msg = await message.answer("<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Нельзя выдать варн офицеру Авангарда.")
        asyncio.create_task(delete_later(msg, 5))
        return

    # 3. Добавляем варн
    current_warns = add_warn(target_id)

    mention = f"<a href='tg://user?id={target_id}'>{name}</a>"
    
    if current_warns >= 3:
        # Увеличиваем счетчик циклов (сколько раз он уже получал бан за варны)
        cursor.execute("UPDATE users SET warn_cycles = warn_cycles + 1 WHERE user_id = ?", (target_id,))
        conn.commit()
        
        # Получаем кол-во циклов
        cursor.execute("SELECT warn_cycles FROM users WHERE user_id = ?", (target_id,))
        cycles = cursor.fetchone()[0]
        
        # Считаем время: 2 часа + (циклы-1) * 1 час. 
        # Если циклов 1 (первый раз), то 2 часа. Если 2, то 3 часа.
        mute_hours = 2 + (cycles - 1)
        until = datetime.now() + timedelta(hours=mute_hours)
        
        try:
            await message.chat.restrict(
                user_id=target_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until
            )
            reset_warns(target_id) # Сбрасываем варны до 0
            
            await message.answer(
                f"<tg-emoji emoji-id='5260293700088511294'>🚫</tg-emoji> <b>{mention}</b> получил 3/3 предупреждений.\n"
                f"Наказание: <b>Мут на {mute_hours} ч.</b> (Рецидив №{cycles})"
            )
        except Exception as e:
            await message.answer(f"Ошибка мута: {e}")
    else:
        # Просто предупреждение
        await message.answer(
            f"<tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> <b>{mention}</b>, это предупреждение! ({current_warns}/3)\n"
            f"При получении 3-го будет выдан мут <b>на 2 часа</b>."
        )

@dp.message(Command("unwarn"))
async def unwarn_command(message: types.Message):
    # 1. Удаляем команду
    try: await message.delete()
    except: pass

    # 2. Проверка прав
    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    is_real_admin = False
    if user_status.status == "creator":
        is_real_admin = True
    elif user_status.status == "administrator" and user_status.can_restrict_members:
        is_real_admin = True

    if not is_real_admin:
    # (Опционально) await message.reply("У тебя нет прав банить.")
        return

    if not message.reply_to_message:
        return

    target_id = message.reply_to_message.from_user.id
    name = message.reply_to_message.from_user.first_name

    # 3. Снимаем варн
    try:
        # Сначала получаем текущее кол-во
        cursor.execute('SELECT warns FROM users WHERE user_id = ?', (target_id,))
        res = cursor.fetchone()
        current_warns = res[0] if res else 0
        
        if current_warns > 0:
            cursor.execute('UPDATE users SET warns = warns - 1 WHERE user_id = ?', (target_id,))
            conn.commit()

            mention = f"<a href='tg://user?id={target_id}'>{name}</a>"
            
            # Получаем новое значение
            new_warns = current_warns - 1
            await message.answer(f"<tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> С <b>{mention}</b> снято одно предупреждение. ({new_warns}/3)")
        else:
            await message.answer(f"У <b>{name}</b> и так нет предупреждений.")
            
    except Exception as e:
        await log_to_owner(f"Ошибка unwarn: {e}")

@dp.message(Command("warns"))
async def list_warns_command(message: types.Message):
    # Проверка на админа
    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    is_real_admin = False
    if user_status.status == "creator":
        is_real_admin = True
    elif user_status.status == "administrator" and user_status.can_restrict_members:
        is_real_admin = True

    if not is_real_admin:
    # (Опционально) await message.reply("У тебя нет прав банить.")
        return

    cursor.execute("SELECT user_id, name, warns FROM users WHERE warns > 0 ORDER BY warns DESC")
    rows = cursor.fetchall()
    
    if not rows:
        await message.reply("<tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> В Башне порядок. Нарушителей нет.")
        return
        
    text = "<b><tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> Список нарушителей:</b>\n\n"
    for uid, name, warns in rows:
        text += f"• <a href='tg://user?id={uid}'>{name}</a> — {warns}/3\n"
        
    await message.reply(text)

#-------------------------------------------------------------------------------------------------------------------ТЕНЕВОЙ МУТ
@dp.message(Command("amute"))
async def amute_command(message: types.Message):
    try: await message.delete()
    except: pass

    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    is_real_admin = False
    if user_status.status == "creator":
        is_real_admin = True
    elif user_status.status == "administrator" and user_status.can_restrict_members:
        is_real_admin = True

    if not is_real_admin:
    # (Опционально) await message.reply("У тебя нет прав банить.")
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
        SILENT_MODE_USERS[target_id] = datetime.now() + timedelta(days=36500)
        save_silent()
        await message.answer(f"<tg-emoji emoji-id='5260293700088511294'>🚫</tg-emoji> <b>{name}</b> отправлен в теневой бан. Его сообщения будут исчезать.")
    else:
        msg = await message.answer(f"{name} уже в муте.")
        asyncio.create_task(delete_later(msg, 5))

@dp.message(Command("unamute"))
async def unamute_command(message: types.Message):
    try: await message.delete()
    except: pass

    user_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
    is_real_admin = False
    if user_status.status == "creator":
        is_real_admin = True
    elif user_status.status == "administrator" and user_status.can_restrict_members:
        is_real_admin = True

    if not is_real_admin:
    # (Опционально) await message.reply("У тебя нет прав банить.")
        return

    if not message.reply_to_message:
        return

    target_id = message.reply_to_message.from_user.id
    name = message.reply_to_message.from_user.first_name

    if target_id in SILENT_MODE_USERS:
        del SILENT_MODE_USERS[target_id] # Удаляем ключ из словаря
        save_silent()
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
        msg = await message.answer(f"<tg-emoji emoji-id='5395444784611480792'>✏️</tg-emoji> {username} записан! ({current_count}/{needed})")
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

#-------------------------------------------------------------------------------------------------------------------КОМАНДА /HELP
@dp.message(Command("help"))
async def help_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Гайд по боту", url=BOT_GUIDE)],
        [InlineKeyboardButton(text="♥️ Поддержать разработчиков", url="https://pay.cloudtips.ru/p/8f3e39da")]
    ])
    await message.answer(
        "Made by yagraze, pan1q & fimgreen.\n"
        "<tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji> ЖМИ <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        reply_markup=keyboard
    )
    asyncio.create_task(delete_later(message, 5))

#-------------------------------------------------------------------------------------------------------------------КОМАНДА /SUMMARY
@dp.message(Command("summary"))
async def summary_command(message: types.Message):
    global SUMMARY_COOLDOWN_TIME
    
    now = datetime.now()
    if message.chat.id != CHAT_ID:
        msg = await message.reply("Отвечу только в чате Барахолки, а не в этой помойке.")
        asyncio.create_task(delete_later(msg, 5))
        return
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
CLASS_ICONS = {
    # КРАСНЫЕ (Игрок 1 / Атакующий)
    "p1_hunter": "<tg-emoji emoji-id='5224477718699087098'>🐍</tg-emoji>",
    "p1_warlock": "<tg-emoji emoji-id='5224220660611457213'>🦅</tg-emoji>",
    "p1_titan": "<tg-emoji emoji-id='5224596865386842527'>🦁</tg-emoji>",
    
    # СИНИЕ (Игрок 2 / Защитник)
    "p2_hunter": "<tg-emoji emoji-id='5224673028041903796'>🐍</tg-emoji>",
    "p2_warlock": "<tg-emoji emoji-id='5224477937742414397'>🦅</tg-emoji>",
    "p2_titan": "<tg-emoji emoji-id='5224305310121892751'>🦁</tg-emoji>",
    
    # НЕЙТРАЛЬНЫЕ (Меню выбора / Старт)
    "neutral_1": "<tg-emoji emoji-id='5226565403517423086'>👶</tg-emoji>",
    "neutral_2": "<tg-emoji emoji-id='5226508538150423514'>👧</tg-emoji>"
}

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
        f"<b>{CLASS_ICONS['neutral_1']} Страж №1:</b> {att_name}\n"
        f"<b>{CLASS_ICONS['neutral_2']} Страж №2:</b> {def_name}\n\n"
        f"<b><tg-emoji emoji-id='5334544901428229844'>ℹ️</tg-emoji> Сетапы классов:</b>\n"
        f"<tg-emoji emoji-id='5224674368071699727'>🐍</tg-emoji> - Ханты: ГГ & Сияние;\n"
        f"<tg-emoji emoji-id='5224259534360447096'>🦅</tg-emoji> - Варлоки: Нова & Пожирание;\n"
        f"<tg-emoji emoji-id='5224282319161954546'>🦁</tg-emoji> - Титаны: ТКраш & Усиление.\n"
        f"<b><tg-emoji emoji-id='5334544901428229844'>ℹ️</tg-emoji> Оружие на выбор:</b>\n"
        f"<tg-emoji emoji-id='5244894167863166109'>🃏</tg-emoji> - Пиковый Туз;\n"
        f"<tg-emoji emoji-id='5472003139303409777'>🤠</tg-emoji> - Ластворд;\n"
        f"<tg-emoji emoji-id='5199852661146422050'>🧪</tg-emoji> - Шип.\n\n"
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
        max_hp = 135
        bar_len = 10 # Длина полоски
        
        # Считаем сколько блоков закрасить (процент от макс хп)
        filled_len = int(round(bar_len * hp / float(max_hp)))
        
        # Защита от выхода за границы [0, bar_len]
        filled_len = max(0, min(bar_len, filled_len))
        
        return "▓" * filled_len + "░" * (bar_len - filled_len)

    p1 = game["p1"]
    p2 = game["p2"]
    
    current_player = p1 if game["turn"] == p1["id"] else p2
    current_class = current_player["class"]
    current_weapon = current_player["weapon"] # ace или lw
    current_name = current_player["name"]

    ru_classes = {"hunter": "<tg-emoji emoji-id='5224674368071699727'>🐍</tg-emoji>", "warlock": "<tg-emoji emoji-id='5224259534360447096'>🦅</tg-emoji>", "titan": "<tg-emoji emoji-id='5224282319161954546'>🦁</tg-emoji>"}
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

    icon1 = CLASS_ICONS.get(f"p1_{p1['class']}", CLASS_ICONS["neutral_1"])
    icon2 = CLASS_ICONS.get(f"p2_{p2['class']}", CLASS_ICONS["neutral_2"])
    
    text = (
        f"<tg-emoji emoji-id='5408935401442267103'>⚔️</tg-emoji> <b>{title}</b>\n\n"
        f"{icon1} <b>{p1['name']}</b>: {p1['hp']} HP{p1_status}\n"
        f"[{get_hp_bar(p1['hp'])}]\n\n"
        f"{icon2} <b>{p2['name']}</b>: {p2['hp']} HP{p2_status}\n"
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

        icon1 = CLASS_ICONS.get(f"p1_{game['p1']['class']}", CLASS_ICONS["neutral_1"])
        icon2 = CLASS_ICONS.get(f"p2_{game['p2']['class']}", CLASS_ICONS["neutral_2"])
        
        text = (
            f"<tg-emoji emoji-id='5442864698187856287'>👜</tg-emoji> <b>ВЫБОР СНАРЯЖЕНИЯ</b>\n\n"
            f"{icon1} <b>{game['p1']['name']}:</b> {get_status(game['p1'])}\n"
            f"{icon2} <b>{game['p2']['name']}:</b> {get_status(game['p2'])}\n\n"
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
                "id": attacker_id, "name": att_name, "hp": 120, 
                "class": None, "weapon": None, # Новое поле
                "ace_streak": 0, "poison_turns": 0, "buff_dmg": 0, "buff_heal": False, "buff_def": 0
            },
            "p2": {
                "id": defender_id, "name": def_name, "hp": 120, 
                "class": None, "weapon": None, # Новое поле
                "ace_streak": 0, "poison_turns": 0, "buff_dmg": 0, "buff_heal": False, "buff_def": 0
            },
            "state": "choosing_class",
            "turn_count": 0,
            "full_log": [],
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

        i1 = CLASS_ICONS["neutral_1"]
        i2 = CLASS_ICONS["neutral_2"]
        
        text = (
            f"<tg-emoji emoji-id='5442864698187856287'>👜</tg-emoji> <b>ВЫБОР СНАРЯЖЕНИЯ</b>\n\n"
            f"{i1} <b>{att_name}:</b> Выбор...\n"
            f"{i2} <b>{def_name}:</b> Выбор...\n\n"
            f"1. Выбери Класс\n2. Выбери Оружие"
        )

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return

#-------------------------------------------------------------------------------------------------------------------БАФФЫ (АБИЛКИ)
    if action in ["duel_buff_radiant", "duel_buff_devour", "duel_buff_amplify"]:
        game_id = callback.message.message_id

        if game_id not in GAME_LOCKS:
            GAME_LOCKS[game_id] = asyncio.Lock()
        
        async with GAME_LOCKS[game_id]:
            if game_id not in ACTIVE_DUELS: return
            game = ACTIVE_DUELS[game_id]
            if callback.from_user.id != game["turn"]:
                await callback.answer("Не твой ход!", show_alert=True)
                return
            game["turn_count"] += 1 
            if callback.from_user.id == game["p1"]["id"]:
                caster, enemy = game["p1"], game["p2"]
            else:
                caster, enemy = game["p2"], game["p1"]

            buff_name = ""
            log_msg = ""
            combo_triggered = False # Флаг комбо
            
            # --- СИЯНИЕ (HUNTER) ---
            if action == "duel_buff_radiant" and caster["class"] == "hunter":
                if caster.get("buff_dmg", 0) > 0:
                    await callback.answer("Сияние уже активно!", show_alert=True); return
                
                caster["buff_dmg"] = 10 # Урон следующего выстрела
                
                # Мгновенный урон 5
                enemy["hp"] -= 5
                if enemy["hp"] < 0: enemy["hp"] = 0
                
                buff_name = "💥 Сияние"
                log_msg = f"{caster['name']} активирует <tg-emoji emoji-id='5472158054478810637'>💥</tg-emoji> <b>Сияние</b>! {enemy['name']} обожжен (-5 HP). След. выстрел +10 урона."
                timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%H:%M:%S")
                clean_msg = clean_log_text(log_msg)
                turn_num = game.get("turn_count", 1)
                game["full_log"].append(f"[{timestamp} | Ход {turn_num}] {clean_msg}")
                save_duels()
            # --- ПОЖИРАНИЕ (WARLOCK) ---
            elif action == "duel_buff_devour" and caster["class"] == "warlock":
                if caster.get("buff_heal"):
                    await callback.answer("Пожирание уже активно!", show_alert=True); return
                
                caster["buff_heal"] = True
                
                # Мгновенный хил 4
                caster["hp"] += 4
                if caster["hp"] > 135: caster["hp"] = 135 # Кап 135
                
                buff_name = "🩸 Пожирание"
                log_msg = f"{caster['name']} активирует <tg-emoji emoji-id='5474317667114457231'>🩸</tg-emoji> <b>Пожирание</b>! Восстановлено 4 HP. След. попадание исцелит 11 HP."
                timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%H:%M:%S")
                clean_msg = clean_log_text(log_msg)
                turn_num = game.get("turn_count", 1)
                game["full_log"].append(f"[{timestamp} | Ход {turn_num}] {clean_msg}")
                save_duels()
            # --- УСИЛЕНИЕ (TITAN) ---
            elif action == "duel_buff_amplify" and caster["class"] == "titan":
                if caster.get("buff_def", 0) > 0:
                    await callback.answer("Усиление уже активно!", show_alert=True); return
                
                caster["buff_def"] = 15
                buff_name = "⚡️ Усиление"
                log_msg = f"{caster['name']} получает <tg-emoji emoji-id='5472175852823282918'>⚡️</tg-emoji> <b>Усиление</b>! След. урон по нему снижен на 15."
            else:
                await callback.answer("Не твой класс!", show_alert=True)
                return

            # ПРОВЕРКА ПОБЕДЫ (ЕСЛИ УБИЛ СИЯНИЕМ)
            if enemy["hp"] <= 0:
                update_duel_stats(caster['id'], True); update_duel_stats(enemy['id'], False)
                
                unique_log = []
                if game.get("full_log"):
                    prev_line = ""
                    for line in game["full_log"]:
                        # Сравниваем с предыдущей строкой (игнорируя пробелы)
                        if line.strip() != prev_line.strip():
                            unique_log.append(line)
                            prev_line = line
                
                # Создаем итоговый текст из уникальных строк
                log_content = "\n".join(unique_log)
                file_name = f"duel_log_{game_id}.txt"
                
                winner_name = caster['name']
                # (или возьми shooter['name'], если это блок стрельбы)
                
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(
                        f"⚔️ ДУЭЛЬ: {game['p1']['name']} vs {game['p2']['name']}\n"
                        f"🏆 ПОБЕДИТЕЛЬ: {winner_name}\n"
                        f"🔢 ВСЕГО ХОДОВ: {turn_num}\n\n"
                        f"{log_content}"
                    )
                
                # Отправляем файл
                log_file = FSInputFile(file_name)
                msg = await bot.send_document(
                    chat_id=callback.message.chat.id,
                    document=log_file,
                    caption="<tg-emoji emoji-id='5373251851074415873'>📝</tg-emoji> Логи Дуэли",
                    reply_to_message_id=callback.message.message_id
                )
                asyncio.create_task(delete_later(msg, 180))
                os.remove(file_name) # Удаляем файл с диска
                
                del ACTIVE_DUELS[game_id]; save_duels()
                if game_id in GAME_LOCKS: del GAME_LOCKS[game_id]
                
                await callback.message.edit_text(f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n<tg-emoji emoji-id='5312241539987020022'>🔥</tg-emoji> {enemy['name']} сгорел заживо!", reply_markup=None)
                await callback.answer(); return

            # --- 2. ТИК ЯДА И КОМБО ---
            if enemy["poison_turns"] > 0:
                poison_dmg = 11
                enemy["poison_turns"] -= 1
                
                # КОМБО СИЯНИЯ (Если только что нажали или висело)
                # Проверяем caster["buff_dmg"], который мы только что поставили
                if caster.get("buff_dmg", 0) > 0 and action == "duel_buff_radiant":
                    poison_dmg += 10 # 11 + 10 = 21 урона от яда + 5 от активации = 26
                    caster["buff_dmg"] = 0 # Тратим бафф
                    combo_triggered = True
                    log_msg = f"<tg-emoji emoji-id='5472158054478810637'>💥</tg-emoji> <b>Сияющий яд!</b> {caster['name']} сжигает врага заживо!\n(<b>-26 HP</b>!)"
                
                elif caster.get("buff_dmg", 0) > 0:
                    # Если бафф висел с прошлого хода (не комбо нажатия, а просто стечение обстоятельств)
                    poison_dmg += 10
                    caster["buff_dmg"] = 0
                    log_msg += " (<tg-emoji emoji-id='5472158054478810637'>💥</tg-emoji> +10 dmg от Сияния!)"

                # КОМБО ПОЖИРАНИЯ (Если только что нажали)
                if caster.get("buff_heal") and action == "duel_buff_devour":
                    caster["hp"] += 11 # 11 хил от яда + 4 от активации = 15
                    if caster["hp"] > 135: caster["hp"] = 135
                    caster["buff_heal"] = False # Тратим бафф
                    combo_triggered = True
                    log_msg = f"<tg-emoji emoji-id='5472233882126419653'>🩸</tg-emoji> <b>Исцеляющий яд!</b> {caster['name']} наносит 11 урона!\n(<b>+15 HP</b>!)"
                
                elif caster.get("buff_heal"):
                    # Если висело с прошлого хода
                    caster["hp"] += 11
                    if caster["hp"] > 135: caster["hp"] = 135
                    caster["buff_heal"] = False
                    log_msg += " (<tg-emoji emoji-id='5472233882126419653'>🩸</tg-emoji> +11 HP от яда!)"

                # УЧЕТ ЩИТА ВРАГА
                if enemy.get("buff_def", 0) > 0:
                    blocked = min(poison_dmg, enemy["buff_def"])
                    poison_dmg -= blocked
                    enemy["buff_def"] -= blocked
                    if combo_triggered:
                        log_msg += f" (<tg-emoji emoji-id='5472175852823282918'>⚡️</tg-emoji> Заблокировано: -{blocked})"
                    else:
                        log_msg += f" (<tg-emoji emoji-id='5472175852823282918'>⚡️</tg-emoji> -{blocked})"

                # НАНЕСЕНИЕ УРОНА ЯДОМ
                enemy["hp"] -= poison_dmg
                
                # Проверка смерти
                if enemy["hp"] <= 0:
                    enemy["hp"] = 0
                    update_duel_stats(caster['id'], True); update_duel_stats(enemy['id'], False)
                    # ГЕНЕРАЦИЯ ФАЙЛА
                    unique_log = []
                    if game.get("full_log"):
                        prev_line = ""
                        for line in game["full_log"]:
                            # Сравниваем с предыдущей строкой (игнорируя пробелы)
                            if line.strip() != prev_line.strip():
                                unique_log.append(line)
                                prev_line = line
                
                    # Создаем итоговый текст из уникальных строк
                    log_content = "\n".join(unique_log)
                    file_name = f"duel_log_{game_id}.txt"
                
                    winner_name = caster['name']
                # (или возьми shooter['name'], если это блок стрельбы)
                
                    with open(file_name, "w", encoding="utf-8") as f:
                        f.write(
                            f"⚔️ ДУЭЛЬ: {game['p1']['name']} vs {game['p2']['name']}\n"
                            f"🏆 ПОБЕДИТЕЛЬ: {winner_name}\n"
                            f"🔢 ВСЕГО ХОДОВ: {turn_num}\n\n"
                            f"{log_content}"
                        )
                
                    # Отправляем файл
                    log_file = FSInputFile(file_name)
                    msg = await bot.send_document(
                        chat_id=callback.message.chat.id,
                        document=log_file,
                        caption="<tg-emoji emoji-id='5373251851074415873'>📝</tg-emoji> Логи Дуэли",
                        reply_to_message_id=callback.message.message_id
                    )
                    asyncio.create_task(delete_later(msg, 180))
                    os.remove(file_name) # Удаляем файл с диска
                    if game_id in GAME_LOCKS: del GAME_LOCKS[game_id]
                    del ACTIVE_DUELS[game_id]; save_duels()
                    await callback.message.edit_text(f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> {enemy['name']} погиб от яда!", reply_markup=None)
                    await callback.answer(); return
                    
            timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%H:%M:%S")
            clean_msg = clean_log_text(log_msg)
            turn_num = game.get("turn_count", 1)
            game["full_log"].append(f"[{timestamp} | Ход {turn_num}] {clean_msg}")
            save_duels()
            
            # ЛОГИКА ТИТАНА (В БЛОКЕ БАФФОВ)
            flying_titan_id = game.get("pending_crash")
            if flying_titan_id:
                titan_id = flying_titan_id
                titan = game["p1"] if game["p1"]["id"] == titan_id else game["p2"]
                enemy_pl = game["p1"] if game["p1"]["id"] != titan_id else game["p2"]
                game["crash_turns"] -= 1
                if game["crash_turns"] <= 0:
                    game["pending_crash"] = None
                    
                    # 1. Прямое попадание (11%)
                    if random.randint(1, 100) <= 11:
                        enemy_pl["hp"] = 0
                        crash_msg = f"<tg-emoji emoji-id='5456140674028019486'>⚡️</tg-emoji> <b>БУУУМ!</b> {titan['name']} размазал соперника! (-100 HP)"
                        timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%H:%M:%S")
                        turn_num = game.get("turn_count", 1)
                        game["full_log"].append(f"[{timestamp} | Ход {turn_num}] {clean_log_text(crash_msg)}")
                        update_duel_stats(titan['id'], True); update_duel_stats(enemy_pl['id'], False)
                        # ГЕНЕРАЦИЯ ФАЙЛА
                        unique_log = []
                        if game["full_log"]:
                            unique_log.append(game["full_log"][0]) # Первая всегда уникальна
                            for line in game["full_log"][1:]:
                                if line != unique_log[-1]: # Если не равна предыдущей
                                    unique_log.append(line)
                
                        log_content = "\n".join(unique_log)
                        file_name = f"duel_log_{game_id}.txt"
                
                        winner_name = titan['name']
                # (или возьми shooter['name'], если это блок стрельбы)
                
                        with open(file_name, "w", encoding="utf-8") as f:
                            f.write(
                                f"⚔️ ДУЭЛЬ: {game['p1']['name']} vs {game['p2']['name']}\n"
                                f"🏆 ПОБЕДИТЕЛЬ: {winner_name}\n"
                                f"🔢 ВСЕГО ХОДОВ: {turn_num}\n\n"
                                f"{log_content}"
                            )
                
                        # Отправляем файл
                        log_file = FSInputFile(file_name)
                        msg = await bot.send_document(
                            chat_id=callback.message.chat.id,
                            document=log_file,
                            caption="<tg-emoji emoji-id='5373251851074415873'>📝</tg-emoji> Логи Дуэли",
                            reply_to_message_id=callback.message.message_id
                        )
                        asyncio.create_task(delete_later(msg, 180))
                        os.remove(file_name) # Удаляем файл с диска
                        if game_id in GAME_LOCKS: del GAME_LOCKS[game_id]
                        del ACTIVE_DUELS[game_id]; save_duels()
                        msg = f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n{crash_msg}"
                        await callback.message.edit_text(msg, reply_markup=None)
                        await callback.answer(); return
                    else:
                        # 2. Промах -> Лужа (20 урона)
                        splash_dmg = 7
                        if enemy_pl.get("buff_def", 0) > 0:
                            blocked = min(splash_dmg, enemy_pl["buff_def"])
                            splash_dmg -= blocked
                            enemy_pl["buff_def"] -= blocked
                        enemy_pl["hp"] -= splash_dmg
                        if enemy_pl["hp"] < 0: enemy_pl["hp"] = 0
                            
                        extra_log = f"\n\n<tg-emoji emoji-id='5456140674028019486'>⚡️</tg-emoji> Титан промахнулся, но задел <b>лужей</b> (-7 HP)!"

                        # --- ЗАПИСЬ В ИСТОРИЮ ---
                        timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%H:%M:%S")
                        # Соединяем log_msg (выстрел врага) и extra_log (приземление)
                        extra_clean = clean_log_text(extra_log) # (Твоя функция очистки)
                        game["full_log"].append(f"[{timestamp} | Ход {turn_num}] {extra_clean}")
                    
                        # Если враг умер от лужи
                        if enemy_pl["hp"] <= 0:
                            update_duel_stats(titan['id'], True); update_duel_stats(enemy_pl['id'], False)
                            unique_log = []
                            if game["full_log"]:
                                unique_log.append(game["full_log"][0]) # Первая всегда уникальна
                                for line in game["full_log"][1:]:
                                    if line != unique_log[-1]: # Если не равна предыдущей
                                        unique_log.append(line)
                
                            log_content = "\n".join(unique_log)
                            file_name = f"duel_log_{game_id}.txt"
                
                            winner_name = titan['name']
                            # (или возьми shooter['name'], если это блок стрельбы)
                
                            with open(file_name, "w", encoding="utf-8") as f:
                                f.write(
                                    f"⚔️ ДУЭЛЬ: {game['p1']['name']} vs {game['p2']['name']}\n"
                                    f"🏆 ПОБЕДИТЕЛЬ: {winner_name}\n"
                                    f"🔢 ВСЕГО ХОДОВ: {turn_num}\n\n"
                                    f"{log_content}"
                                )
                
                            # Отправляем файл
                            log_file = FSInputFile(file_name)
                            msg = await bot.send_document(
                                chat_id=callback.message.chat.id,
                                document=log_file,
                                caption="<tg-emoji emoji-id='5373251851074415873'>📝</tg-emoji> Логи Дуэли",
                                reply_to_message_id=callback.message.message_id
                            )
                            asyncio.create_task(delete_later(msg, 180))
                            os.remove(file_name) # Удаляем файл с диска
                            if game_id in GAME_LOCKS: del GAME_LOCKS[game_id]
                            del ACTIVE_DUELS[game_id]; save_duels()
                            await callback.message.edit_text(f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n<tg-emoji emoji-id='5456140674028019486'>⚡️</tg-emoji> {enemy_pl['name']} погиб от электричества.", reply_markup=None)
                            await callback.answer(); return

                        game["log"] = f"{log_msg}{extra_log}"
                        game["turn"] = titan_id # Ход Титану
                else:
                    game["log"] = f"{log_msg}\n<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> Титан летит! Осталось ходов: {game['crash_turns']}!"
                    game["turn"] = caster["id"] # Ход остается у тебя
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
        if game_id not in GAME_LOCKS:
            GAME_LOCKS[game_id] = asyncio.Lock()

        async with GAME_LOCKS[game_id]:
            if game_id not in ACTIVE_DUELS: return
            game = ACTIVE_DUELS[game_id]
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
            game["turn_count"] += 1 
            damage = 0
            hits_count = 0
            log_msg = ""
            healed_amount = 0
            
#-------------------------------------------------------------------------------------------------------------------ЛОГИКА ОРУЖИЯ

            if action == "duel_shoot_primary":
                weapon_type = shooter["weapon"]
                
                # --- ЛОГИКА ТУЗА ---
                if weapon_type == "ace":
                    update_usage(shooter_id, "w_ace")
                    weapon_name = "<tg-emoji emoji-id='5244894167863166109'>🃏</tg-emoji> Пиковый Туз"
                    shooter["ace_streak"] = shooter.get("ace_streak", 0)
                    
                    roll = random.randint(1, 100)
                    
                    # Если бафф уже есть (попал в прошлый раз)
                    if shooter["ace_streak"] > 0:
                        # 25% шанс на Мементо (50 урона)
                        if roll <= 25:
                            damage = 50
                            shooter["ace_streak"] = 1 # Стрик сохраняется
                            log_msg = f"<tg-emoji emoji-id='5276032951342088188'>💥</tg-emoji> <b>MEMENTO MORI!</b> {shooter['name']} критует Тузом на {damage}!"
                        # 45% шанс на обычный (25 урона)
                        elif roll <= (25 + 45):
                            damage = 25
                            shooter["ace_streak"] = 1 # Стрик сохраняется
                            log_msg = f"<tg-emoji emoji-id='5379748062124056162'>❗️</tg-emoji> <b>Попадание!</b> {shooter['name']} наносит Тузом {damage} урона."
                        # Иначе промах
                        else:
                            damage = 0
                            shooter["ace_streak"] = 0 # Стрик теряется
                            log_msg = f"<tg-emoji emoji-id='5467538555158943525'>💭</tg-emoji> <b>Промах!</b> {shooter['name']} мажет с Туза."
                    
                    # Если баффа нет (первый выстрел или после промаха)
                    else:
                        if roll <= 45:
                            damage = 25
                            shooter["ace_streak"] = 1 # Получаем стрик
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
                        if random.randint(1, 100) <= 50:
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
                    update_usage(shooter_id, "w_thorns")
                    weapon_name = "<tg-emoji emoji-id='5199852661146422050'>🧪</tg-emoji> Шип"
                    shooter["ace_streak"] = 0
                
                    if random.randint(1, 100) <= 50:
                        hit = True
                        damage = 29
                        
                        # Если яд уже был, он тикает ПЕРЕД обновлением
                        if target["poison_turns"] > 0:
                            damage += 11 # Добавляем тик яда к урону выстрела
                            log_msg = f"<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> <b>Попадание!</b> {shooter['name']} отравляет врага Шипом! (40 урона + Яд)"
                        else:
                            log_msg = f"<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> <b>Попадание!</b> {shooter['name']} отравляет врага Шипом! (29 урона + Яд)."
                            
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
                    target["hp"] -= 11
                    target["poison_turns"] -= 1
                    poison_msg = f"\n🧪 Яд сжигает {target['name']} (-11 HP)!"
                    if target["hp"] <= 0:
                        # (Победа Титана)
                        target["hp"] = 0
                        update_duel_stats(shooter['id'], True); update_duel_stats(target['id'], False)
                        # ГЕНЕРАЦИЯ ФАЙЛА
                        unique_log = []
                        if game["full_log"]:
                            unique_log.append(game["full_log"][0]) # Первая всегда уникальна
                            for line in game["full_log"][1:]:
                                if line != unique_log[-1]: # Если не равна предыдущей
                                    unique_log.append(line)
                
                        log_content = "\n".join(unique_log)
                        file_name = f"duel_log_{game_id}.txt"
                
                        winner_name = shooter['name']
                        # (или возьми shooter['name'], если это блок стрельбы)
                
                        with open(file_name, "w", encoding="utf-8") as f:
                            f.write(
                                f"⚔️ ДУЭЛЬ: {game['p1']['name']} vs {game['p2']['name']}\n"
                                f"🏆 ПОБЕДИТЕЛЬ: {winner_name}\n"
                                f"🔢 ВСЕГО ХОДОВ: {turn_num}\n\n"
                                f"{log_content}"
                            )
                
                        # Отправляем файл
                        log_file = FSInputFile(file_name)
                        msg = await bot.send_document(
                            chat_id=callback.message.chat.id,
                            document=log_file,
                            caption="<tg-emoji emoji-id='5373251851074415873'>📝</tg-emoji> Логи Дуэли",
                            reply_to_message_id=callback.message.message_id
                        )
                        asyncio.create_task(delete_later(msg, 180))
                        os.remove(file_name) # Удаляем файл с диска
                        if game_id in GAME_LOCKS: del GAME_LOCKS[game_id]
                        del ACTIVE_DUELS[game_id]; save_duels()
                        await callback.message.edit_text(f"🏆 <b>ПОБЕДА!</b>{poison_msg}\n⚡ Титан улетел, а враг умер от яда.", reply_markup=None)
                        await callback.answer(); return
                else:
                    poison_msg = ""
                game["pending_crash"] = shooter_id 
                game["crash_turns"] = 1
                game["turn"] = target["id"]   
                crash_text = f"<tg-emoji emoji-id='5456140674028019486'>⚡️</tg-emoji> <b>ГРОМ!</b> {shooter['name']} прожал ульту!"
                game["log"] = crash_text + poison_msg
                timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%H:%M:%S")
                turn_num = game.get("turn_count", 1)
                clean_txt = clean_log_text(crash_text + poison_msg)
                game["full_log"].append(f"[{timestamp} | Ход {turn_num}] {clean_txt}")
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
                shooter["hp"] += 11
                if shooter["hp"] > 135: shooter["hp"] = 135
                shooter["buff_heal"] = False # Сгорает
                log_msg += " (<tg-emoji emoji-id='5474317667114457231'>🩸</tg-emoji> +11 HP)"

            # 1. Наносим урон врагу
            if damage > 0:
                target["hp"] -= damage
                if target["hp"] < 0: target["hp"] = 0

            # 2. ТИК ЯДА (У врага, в МОЙ ход)
            # Но есть нюанс: если мы ТОЛЬКО ЧТО попали Шипом, яд не должен тикнуть мгновенно.
            # (По твоим словам: "попадаю, противник ходит, Я делаю ход - дот срабатывает").
            
            is_new_poison = (action == "duel_shoot_primary" and shooter["weapon"] == "thorn" and hit)
            
            if target["poison_turns"] > 0 and not is_new_poison:
                target["hp"] -= 11
                target["poison_turns"] -= 1
                log_msg += f"\n<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> Яд сжигает {target['name']} (-11 HP)!"
                if target["hp"] < 0: target["hp"] = 0

            timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%H:%M:%S")
            clean_msg = clean_log_text(log_msg)
            turn_num = game.get("turn_count", 1)
            game["full_log"].append(f"[{timestamp} | Ход {turn_num}] {clean_msg}")
            
            # 3. ПРОВЕРКА ПОБЕДЫ (От выстрела ИЛИ от яда)
            if target["hp"] <= 0:
                update_duel_stats(shooter['id'], True)
                update_duel_stats(target['id'], False)
                # ГЕНЕРАЦИЯ ФАЙЛА
                unique_log = []
                if game["full_log"]:
                    unique_log.append(game["full_log"][0]) # Первая всегда уникальна
                    for line in game["full_log"][1:]:
                        if line != unique_log[-1]: # Если не равна предыдущей
                            unique_log.append(line)
                
                log_content = "\n".join(unique_log)
                file_name = f"duel_log_{game_id}.txt"
                
                winner_name = shooter['name']
                # (или возьми shooter['name'], если это блок стрельбы)
                
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(
                        f"⚔️ ДУЭЛЬ: {game['p1']['name']} vs {game['p2']['name']}\n"
                        f"🏆 ПОБЕДИТЕЛЬ: {winner_name}\n"
                        f"🔢 ВСЕГО ХОДОВ: {turn_num}\n\n"
                        f"{log_content}"
                    )
                
                # Отправляем файл
                log_file = FSInputFile(file_name)
                msg = await bot.send_document(
                    chat_id=callback.message.chat.id,
                    document=log_file,
                    caption="<tg-emoji emoji-id='5373251851074415873'>📝</tg-emoji> Логи Дуэли",
                    reply_to_message_id=callback.message.message_id
                )
                asyncio.create_task(delete_later(msg, 180))
                os.remove(file_name) # Удаляем файл с диска
                if game_id in GAME_LOCKS: del GAME_LOCKS[game_id]
                del ACTIVE_DUELS[game_id]
                
                # Если умер от яда, а не выстрела, можно поменять текст, но победа все равно моя
                await callback.message.edit_text(f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n<tg-emoji emoji-id='5463186335948878489'>⚰️</tg-emoji> {target['name']} повержен.", reply_markup=None)
                await callback.answer()
                return

            # === ЛОГИКА ПРИЗЕМЛЕНИЯ ТИТАНА (В БЛОКЕ СТРЕЛЬБЫ) ===
            flying_titan_id = game.get("pending_crash")
            
            if flying_titan_id:
                titan_id = flying_titan_id
                titan = game["p1"] if game["p1"]["id"] == titan_id else game["p2"]
                enemy_pl = game["p1"] if game["p1"]["id"] != titan_id else game["p2"]

                if shooter_id != flying_titan_id: # Если стрелял защитник
                    game["crash_turns"] -= 1
                    
                    if game["crash_turns"] <= 0:
                        # ПРИЗЕМЛЕНИЕ
                        game["pending_crash"] = None

                        # ТИК ЯДА (У защитника)
                        if shooter["poison_turns"] > 0:
                            shooter["hp"] -= 11
                            shooter["poison_turns"] -= 1
                            log_msg += f"\n<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> Яд (-11 HP)"
                            timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%H:%M:%S")
                            clean_msg = clean_log_text(log_msg)
                            turn_num = game.get("turn_count", 1)
                            game["full_log"].append(f"[{timestamp} | Ход {turn_num}] {clean_msg}")
                            if shooter["hp"] <= 0:
                                shooter["hp"] = 0
                                update_duel_stats(titan['id'], True); update_duel_stats(shooter['id'], False)
                                # ГЕНЕРАЦИЯ ФАЙЛА
                                unique_log = []
                                if game["full_log"]:
                                    unique_log.append(game["full_log"][0]) # Первая всегда уникальна
                                    for line in game["full_log"][1:]:
                                        if line != unique_log[-1]: # Если не равна предыдущей
                                            unique_log.append(line)
                
                                log_content = "\n".join(unique_log)
                                file_name = f"duel_log_{game_id}.txt"
                
                                winner_name = titan['name']
                                # (или возьми shooter['name'], если это блок стрельбы)
                
                                with open(file_name, "w", encoding="utf-8") as f:
                                    f.write(
                                        f"⚔️ ДУЭЛЬ: {game['p1']['name']} vs {game['p2']['name']}\n"
                                        f"🏆 ПОБЕДИТЕЛЬ: {winner_name}\n"
                                        f"🔢 ВСЕГО ХОДОВ: {turn_num}\n\n"
                                        f"{log_content}"
                                    )
                
                                # Отправляем файл
                                log_file = FSInputFile(file_name)
                                msg = await bot.send_document(
                                    chat_id=callback.message.chat.id,
                                    document=log_file,
                                    caption="<tg-emoji emoji-id='5373251851074415873'>📝</tg-emoji> Логи Дуэли",
                                    reply_to_message_id=callback.message.message_id
                                )
                                asyncio.create_task(delete_later(msg, 180))
                                os.remove(file_name) # Удаляем файл с диска
                                if game_id in GAME_LOCKS: del GAME_LOCKS[game_id]
                                del ACTIVE_DUELS[game_id]; save_duels()
                                await callback.message.edit_text(f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n<tg-emoji emoji-id='5411138633765757782'>🧪</tg-emoji> {shooter['name']} погиб от яда!", reply_markup=None)
                                await callback.answer(); return
                        
                        # УДАР ТИТАНА
                        # 1. Прямое (11%)
                        if random.randint(1, 100) <= 11:
                            enemy_pl["hp"] = 0
                            crash_msg = f"<tg-emoji emoji-id='5456140674028019486'>⚡️</tg-emoji> <b>БУУУМ!</b> {titan['name']} размазал соперника! (-100 HP)"
                            timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%H:%M:%S")
                            turn_num = game.get("turn_count", 1)
                            game["full_log"].append(f"[{timestamp} | Ход {turn_num}] {clean_log_text(crash_msg)}")
                            update_duel_stats(titan['id'], True); update_duel_stats(enemy_pl['id'], False)
                            # ГЕНЕРАЦИЯ ФАЙЛА
                            unique_log = []
                            if game["full_log"]:
                                unique_log.append(game["full_log"][0]) # Первая всегда уникальна
                                for line in game["full_log"][1:]:
                                    if line != unique_log[-1]: # Если не равна предыдущей
                                        unique_log.append(line)
                
                            log_content = "\n".join(unique_log)
                            file_name = f"duel_log_{game_id}.txt"
                
                            winner_name = titan['name']
                            # (или возьми shooter['name'], если это блок стрельбы)
                
                            with open(file_name, "w", encoding="utf-8") as f:
                                f.write(
                                    f"⚔️ ДУЭЛЬ: {game['p1']['name']} vs {game['p2']['name']}\n"
                                    f"🏆 ПОБЕДИТЕЛЬ: {winner_name}\n"
                                    f"🔢 ВСЕГО ХОДОВ: {turn_num}\n\n"
                                    f"{log_content}"
                                )
                
                            # Отправляем файл
                            log_file = FSInputFile(file_name)
                            msg = await bot.send_document(
                                chat_id=callback.message.chat.id,
                                document=log_file,
                                caption="<tg-emoji emoji-id='5373251851074415873'>📝</tg-emoji> Логи Дуэли",
                                reply_to_message_id=callback.message.message_id
                            )
                            asyncio.create_task(delete_later(msg, 180))
                            os.remove(file_name) # Удаляем файл с диска
                            if game_id in GAME_LOCKS: del GAME_LOCKS[game_id]
                            del ACTIVE_DUELS[game_id]; save_duels()
                            msg = f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n{crash_msg}"
                            await callback.message.edit_text(msg, reply_markup=None)
                            await callback.answer(); return
                        else:
                            # 2. Лужа (20 урона)
                            splash_dmg = 7
                            if enemy_pl.get("buff_def", 0) > 0:
                                blocked = min(splash_dmg, enemy_pl["buff_def"])
                                splash_dmg -= blocked
                                enemy_pl["buff_def"] -= blocked
                            enemy_pl["hp"] -= splash_dmg
                            if enemy_pl["hp"] < 0: enemy_pl["hp"] = 0
                            
                            extra_log = f"\n\n<tg-emoji emoji-id='5456140674028019486'>⚡️</tg-emoji> Титан промахнулся, но задел <b>лужей</b> (-7 HP)!"
                            # --- ЗАПИСЬ В ИСТОРИЮ ---
                            timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%H:%M:%S")
                            # Соединяем log_msg (выстрел врага) и extra_log (приземление)
                            extra_clean = clean_log_text(extra_log) # (Твоя функция очистки)
                            game["full_log"].append(f"[{timestamp} | Ход {turn_num}] {extra_clean}")
                            
                            # Если враг умер от лужи
                            if enemy_pl["hp"] <= 0:
                                update_duel_stats(titan['id'], True); update_duel_stats(enemy_pl['id'], False)
                                # ГЕНЕРАЦИЯ ФАЙЛА
                                unique_log = []
                                if game["full_log"]:
                                    unique_log.append(game["full_log"][0]) # Первая всегда уникальна
                                    for line in game["full_log"][1:]:
                                        if line != unique_log[-1]: # Если не равна предыдущей
                                            unique_log.append(line)
                
                                log_content = "\n".join(unique_log)
                                file_name = f"duel_log_{game_id}.txt"
                
                                winner_name = titan['name']
                                # (или возьми shooter['name'], если это блок стрельбы)
                
                                with open(file_name, "w", encoding="utf-8") as f:
                                    f.write(
                                        f"⚔️ ДУЭЛЬ: {game['p1']['name']} vs {game['p2']['name']}\n"
                                        f"🏆 ПОБЕДИТЕЛЬ: {winner_name}\n"
                                        f"🔢 ВСЕГО ХОДОВ: {turn_num}\n\n"
                                        f"{log_content}"
                                    )
                
                                # Отправляем файл
                                log_file = FSInputFile(file_name)
                                msg = await bot.send_document(
                                    chat_id=callback.message.chat.id,
                                    document=log_file,
                                    caption="<tg-emoji emoji-id='5373251851074415873'>📝</tg-emoji> Логи Дуэли",
                                    reply_to_message_id=callback.message.message_id
                                )
                                asyncio.create_task(delete_later(msg, 180))
                                os.remove(file_name) # Удаляем файл с диска
                                if game_id in GAME_LOCKS: del GAME_LOCKS[game_id]
                                del ACTIVE_DUELS[game_id]; save_duels()
                                await callback.message.edit_text(f"<tg-emoji emoji-id='5312315739842026755'>🏆</tg-emoji> <b>ПОБЕДА!</b>\n\n{log_msg}\n\n<tg-emoji emoji-id='5456140674028019486'>⚡️</tg-emoji> {enemy_pl['name']} погиб от электричества.", reply_markup=None)
                                await callback.answer(); return
                            
                            game["log"] = f"{log_msg}{extra_log}"
                            game["turn"] = titan_id
                    
                    else:
                        game["log"] = f"{log_msg}\n<tg-emoji emoji-id='5440660757194744323'>‼️</tg-emoji> Титан летит! Осталось ходов: {game['crash_turns']}!"
                        game["turn"] = shooter_id
            else:
                # ОБЫЧНАЯ СМЕНА ХОДА
                game["turn"] = target["id"]
                game["log"] = log_msg
            save_duels()
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
    is_real_admin = False
    if user_status.status == "creator":
        is_real_admin = True
    elif user_status.status == "administrator" and user_status.can_restrict_members:
        is_real_admin = True

    if not is_real_admin:
    # (Опционально) await message.reply("У тебя нет прав банить.")
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
    is_real_admin = False
    if user_status.status == "creator":
        is_real_admin = True
    elif user_status.status == "administrator" and user_status.can_restrict_members:
        is_real_admin = True

    if not is_real_admin:
    # (Опционально) await message.reply("У тебя нет прав банить.")
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
    user = message.from_user
    uid = user.id
    name = user.first_name
    uname = f"@{user.username}" if user.username else name

    roll = random.randint(1, 100)

    # --- 2. МУТ (AMUTE на время) ---
    if roll <= 26:
        # (Убираем проверку на админа, раз ты хочешь, чтобы и они страдали)
        
        duration = 30 if random.randint(1, 5) == 1 else 15
        end_time = datetime.now() + timedelta(minutes=duration)
        
        SILENT_MODE_USERS[uid] = end_time
        save_silent()
        
        phrase = random.choice(MUTE_CRITICAL_PHRASES) if duration == 30 else random.choice(MUTE_SHORT_PHRASES)
        await message.reply(phrase.replace("@username", uname))

    # --- 3. ПОЗОРНЫЙ ТИТУЛ (10%) --- (27-37)
    elif roll <= 37:
        # Проверяем на админа
        user_status = await bot.get_chat_member(message.chat.id, uid)
        if user_status.status in ["administrator", "creator"]:
            # Если это админ — ему везет, титул не выдается
            text = random.choice(SAFE_PHRASES)
            msg = await message.reply(text.replace("@username", uname))
            asyncio.create_task(delete_later(msg, 15))
            asyncio.create_task(delete_later(message, 15))
            return

        titles = ["ПИДРИЛА", "БАЛБЕС", "ДЫРЯВЫЙ", "ЧМЭС", "ШЛЕПОК", "ЧУЧА", "ЧМОНЯ", "ЛОХ", "СЛАБИ", "ТАПИР", "НН", "ЗЕМЛЕКОП", "BUNGIE DEV", "СЕЙНТ-14", "СОСАЛ"]
        title = random.choice(titles)
        
        emoji = "🍌" # Банан (или что-то похожее)
        if title in ["БАЛБЕС", "ЧМЭС", "ШЛЕПОК", "ЧУЧА", "ЧМОНЯ", "ЛОХ", "СЛАБИ", "НН"]:
            emoji = "🤡"
        
        try:
            # Выдаем "админку без прав" чтобы поставить тайтл
            await bot.promote_chat_member(
                chat_id=message.chat.id,
                user_id=uid,
                is_anonymous=False,
                can_manage_chat=False, # Нужно хоть 1 право? Обычно да, manage_chat безопасно
                can_change_info=False,
                can_post_messages=False,
                can_edit_messages=False,
                can_delete_messages=False,
                can_invite_users=True,
                can_restrict_members=False,
                can_pin_messages=False,
                can_manage_topics=False
            )
            await asyncio.sleep(3)
            await bot.set_chat_administrator_custom_title(message.chat.id, uid, title)
            
            # Запоминаем для реакций
            TAGGED_USERS[uid] = {
                "emoji": emoji,
                "until": datetime.now() + timedelta(hours=1)
            }
            save_tagged()
            
            msg = await message.reply(
                f"<tg-emoji emoji-id='5424818078833715060'>📣</tg-emoji> Именем Барахолки AI и Князя Евгения!\n"
                f"Тебе, {uname}, присуждается почетный статус <b>{title}</b> на 1 час.\n"
                f"Наслаждайся вниманием {emoji}"
            )
            asyncio.create_task(delete_later(msg, 3600))
        except Exception as e:
            await message.reply(f"Хотел выдать титул, но не хватает прав (Add Admins): {e}")

    # --- 4. ПУСТО (49%) ---
    else:
        text = random.choice(SAFE_PHRASES)
        msg = await message.reply(text.replace("@username", uname))
        asyncio.create_task(delete_later(message, 15))
        asyncio.create_task(delete_later(msg, 15))

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
            ],
            [
                InlineKeyboardButton(text="💸 Поддержать канал за новости", url="https://pay.cloudtips.ru/p/bb9b6a35")
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
            "• <tg-emoji emoji-id='5471895155235654649'>2️⃣</tg-emoji> <a href='https://www.bungie.net/ru/ClanV2?groupid=5223067'>Baraholka Community Hub</a>\n"
            "• <tg-emoji emoji-id='5472038418164785413'>1️⃣</tg-emoji> <a href='https://www.bungie.net/en/ClanV2?groupid=5237071'>Baraholka United</a>\n\n"
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

    # --- РЕАКЦИЯ НА МЕЧЕНЫХ (ПОЗОР) ---
    if user_id in TAGGED_USERS:
        data = TAGGED_USERS[user_id]
        if datetime.now() < data["until"]:
            try: await message.react([ReactionTypeEmoji(emoji=data["emoji"])])
            except: pass
        else:
            # Время вышло - снимаем
            del TAGGED_USERS[user_id]
            save_tagged()
            try:
                # Снимаем админку (промоутим в обычного юзера)
                await bot.promote_chat_member(message.chat.id, user_id, can_manage_chat=False) 
                # (В ТГ нельзя "снять" админа, можно только разжаловать, но это может не убрать тайтл.
                # Лучший способ убрать тайтл: promote с пустыми правами и пустым тайтлом, 
                # а потом restrict или просто оставить так).
                
                # Попробуем убрать тайтл:
                await bot.set_chat_administrator_custom_title(message.chat.id, user_id, "Страж")
                # И разжаловать
                await bot.promote_chat_member(
                    chat_id=message.chat.id,
                    user_id=user_id,
                    is_anonymous=False,
                    can_manage_chat=False,
                    can_change_info=False,
                    can_post_messages=False,
                    can_edit_messages=False,
                    can_delete_messages=False,
                    can_invite_users=False,
                    can_restrict_members=False,
                    can_pin_messages=False,
                    can_manage_topics=False
                )
            except: pass

    # Регистрируем чат, если это не личка
    if message.chat.type in ["group", "supergroup"]:
        register_chat(message.chat.id, message.chat.title)
    
    # --- ШПИОНСКИЙ РЕЖИМ ---
    # Если бот пишет НЕ в основном чате и НЕ в ЛС с админом
    if message.chat.id != CHAT_ID and message.chat.id != ADMIN_CHAT_ID and message.chat.id != DEV_CHAT_ID and message.chat.id != OWNER_ID:
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

#-------------------------------------------------------------------------------------------------------------------Graze
    user = message.from_user
    if (user.username and user.username.lower() == "YaGraze") or user.id == 832840031: # Вставь ID
        if random.randint(1, 5) == 1:
            try:
                await message.react([ReactionTypeEmoji(emoji="👨‍💻")])
            except Exception as e:
                await log_to_owner(f"⚠️ Ошибка реакции чемпиона: {e}")

#-------------------------------------------------------------------------------------------------------------------Graze
    user = message.from_user
    if (user.username and user.username.lower() == "fimgreen") or user.id == 969698544: # Вставь ID
        if random.randint(1, 10) == 1:
            try:
                await message.react([ReactionTypeEmoji(emoji="👨‍💻")])
            except Exception as e:
                await log_to_owner(f"⚠️ Ошибка реакции чемпиона: {e}")
            
#-------------------------------------------------------------------------------------------------------------------РЕАКЦИЯ ДЛЯ ПОБЕДИТЕЛЯ ТУРНИРА (ВСЕГДА 🏆)
    user = message.from_user
    if (user.username and user.username.lower() == "pan1q") or user.id == 709473070: # Вставь ID
        if random.randint(1, 100000) == 1:
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

#-------------------------------------------------------------------------------------------------------------------ТЕХПОДДЕРЖКА (СЕРВЕРА)
    server_triggers = [
        "сервера недоступны", "не могу зайти в игру", "ошибка в игре", 
        "что с серверами", "сервера лежат", "что с игрой", "игра не работает", "вылетает с ошибкой", "код ошибки",
        "cabbage", "nightingale", "найтингейл", "weasel", "визл", "визел", "baboon",
        "бесконечная загрузка", "потеряно соединение", "контакт с серверами",
        "destiny 2 не запускается", "серверы рип", "упали сервера",
        "опять дудос", "дудосят", "ддос"
    ]
    
    if any(tr in text_lower for tr in server_triggers):
        help_url = "https://help.bungie.net/hc/ru/sections/360010290252-%D0%9A%D0%BE%D0%B4%D1%8B-%D0%BE%D1%88%D0%B8%D0%B1%D0%BE%D0%BA-Destiny"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔧 Коды ошибок Bungie", url=help_url)]
        ])

        phrases = [
            "<tg-emoji emoji-id='5318773107207447403'>😱</tg-emoji> <b>Может дело в Тапире?</b>\nЕсли нет, то может в игре идет техобслуживание? Глянь посты в канале.",
            "<tg-emoji emoji-id='5318773107207447403'>😱</tg-emoji> <b>У меня всё работает.</b> Может, тебя забанили?\nЛадно, вот ссылка на коды ошибок.",
            "<tg-emoji emoji-id='5318773107207447403'>😱</tg-emoji> <b>Свидетель заблокировал доступ? Или твой провайдер?</b>\nЕсли это не Тапир, то иди читай Bungie Help."
        ]
        
        await message.reply(
            f"{random.choice(phrases)}\nПроверь свою ошибку:",
            reply_markup=kb
        )
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

    # --- РЕПУТАЦИЯ (СПАСИБО) ---
    if message.reply_to_message:
        if message.reply_to_message.is_automatic_forward or message.reply_to_message.from_user.id == 777000:
            return
        target = message.reply_to_message.from_user
        
        # Нельзя благодарить себя и ботов
        if target.id != message.from_user.id and not target.is_bot:
            # Словарь триггеров
            thx_words = ["спасибо", "спс", "сяб", "благодарю", "+", "лучший", "красава", "ты красава", "thx", "ty", "👍", "ты лучший", "❤️"]
            
            # Проверяем, есть ли триггер в начале сообщения (или если сообщение состоит только из него)
            msg_lower = message.text.lower().strip()
            is_thx = any(msg_lower.startswith(w) for w in thx_words)
            
            if is_thx:
                new_rep = add_reputation(target.id)
                target_name = target.first_name
                
                # Пишем ответ
                rep_msg = await message.reply(
                    f"<tg-emoji emoji-id='5397916757333654639'>➕</tg-emoji> <b>{target_name}</b> получает +1 к репутации от {message.from_user.first_name}!\n"
                    f"<tg-emoji emoji-id='5325547803936572038'>✨</tg-emoji> Всего репутации: <b>{new_rep}</b>"
                )
                asyncio.create_task(delete_later(rep_msg, 300))

    # --- ДИЗЛАЙК (МИНУС РЕПУТАЦИЯ) ---
    toxic_words = ["клоун", "-", "токсик", "держи в курсе", "высрал", "насрал", "тролль", "хуйня", "пиздеж", "пиздёж"]
    msg_lower = message.text.lower().strip()
    is_toxic = any(msg_lower.startswith(w) for w in toxic_words)

    if message.reply_to_message and is_toxic:
        # Пропускаем посты канала и сервисные сообщения Telegram
        if message.reply_to_message.is_automatic_forward or message.reply_to_message.from_user.id == 777000:
            return
        target = message.reply_to_message.from_user
        attacker = message.from_user
            
        if target.id != attacker.id and not target.is_bot:
                
            # --- ЛОГИКА ПРОВЕРКИ КД С ТАЙМЕРОМ ---
            if not check_downvote_cooldown(attacker.id):
                # Если КД не прошло, вычисляем сколько осталось
                try:
                    cursor.execute("SELECT last_downvote FROM users WHERE user_id = ?", (attacker.id,))
                    res = cursor.fetchone()
                    if res and res[0]:
                        last_time = datetime.fromisoformat(res[0])
                        # Время, которое прошло с последнего дизлайка
                        delta = datetime.now() - last_time
                        # Сколько нужно ждать (2 часа)
                        cooldown_time = timedelta(hours=2)
                            
                        if delta < cooldown_time:
                            remaining = cooldown_time - delta
                            minutes_left = int(remaining.total_seconds() // 60) + 1
                                
                            cooldown_msg = await message.reply(
                                f"<tg-emoji emoji-id='5440632582209287180'>🕙</tg-emoji> <b>Перезарядка!</b>\n"
                                f"У тебя откат на дизлайки. Попробуй через <b>{minutes_left} мин.</b>"
                            )
                            asyncio.create_task(delete_later(cooldown_msg, 10))
                except Exception as e:
                    print(f"Ошибка таймера КД: {e}")
                    
                return # Прерываем выполнение, репутацию не снимаем

            # Если КД прошло — выполняем наказание
            new_rep = remove_reputation(target.id)
            update_downvote_time(attacker.id)
                
            t_name = target.first_name
            u_name = attacker.first_name
                
            down_msg = await message.reply(
            f"<tg-emoji emoji-id='5246762912428603768'>📉</tg-emoji> <b>{t_name}</b> теряет репутацию из-за {u_name}!\n"
            f"<tg-emoji emoji-id='5325547803936572038'>✨</tg-emoji> Репутация: <b>{new_rep}</b>"
            )
            asyncio.create_task(delete_later(down_msg, 300))
    
#-------------------------------------------------------------------------------------------------------------------ИИ (ТОЛЬКО ПО ТЕГУ + КУЛДАУН)
    bot_info = await bot.get_me()

    is_mention = f"@{bot_info.username}" in message.text

    if is_mention:
        if message.chat.id != CHAT_ID:
            msg = await message.reply("Я разговариваю только с элитой в чате Барахолки.")
            asyncio.create_task(delete_later(msg, 5))
            return
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
                f"Обратись ко мне через <b>{minutes_left} мин</b>, когда пойду траву потрогать. <tg-emoji emoji-id='5469629323763796670'>🙄</tg-emoji>"
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

    print(f"⏰ ВРЕМЯ СЕРВЕРА: {datetime.now()}")

    asyncio.create_task(check_silence_loop())

    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(send_morning_voice, "cron", hour=7, minute=00, timezone=pytz.timezone("Europe/Moscow"))

    scheduler.start()

    dp.message.middleware(SilentModeMiddleware())
    
    dp.message.middleware(AntiFloodMiddleware())

    asyncio.create_task(check_tagged_users())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

