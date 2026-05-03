import asyncio
import logging
import sqlite3
import html
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

BOT_TOKEN = "8644503362:AAEPogfQT9w91J3lErAaqeGqMUEjEthZcFU"
OWNER_ID = 5618715354

# Исправленное логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------- БАЗА ДАННЫХ ----------
def init_db():
    conn = sqlite3.connect("hamam.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            level INTEGER DEFAULT 1,
            coins INTEGER DEFAULT 0,
            burmalda INTEGER DEFAULT 0,
            vip_until TEXT,
            last_hamam TEXT,
            cooldown_bonus INTEGER DEFAULT 0,
            last_turkish TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS duels (
            challenger_id INTEGER,
            opponent_id INTEGER,
            challenge_time TEXT,
            chat_id INTEGER,
            message_id INTEGER
        )
    ''')
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    if 'burmalda' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN burmalda INTEGER DEFAULT 0")
    if 'cooldown_bonus' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN cooldown_bonus INTEGER DEFAULT 0")
    if 'last_turkish' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN last_turkish TEXT")
    c.execute("PRAGMA table_info(duels)")
    duel_columns = [col[1] for col in c.fetchall()]
    if 'chat_id' not in duel_columns:
        c.execute("ALTER TABLE duels ADD COLUMN chat_id INTEGER")
    if 'message_id' not in duel_columns:
        c.execute("ALTER TABLE duels ADD COLUMN message_id INTEGER")
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

init_db()

# ... (остальные функции: get_user, save_user, is_vip, get_effective_cooldown,
# update_hamam, update_turkish_bath, reduce_cooldown, add_coins_to_user,
# add_burmalda_to_user, maybe_send_sticker, get_duel_winner,
# get_choice_keyboard, get_accept_keyboard, set_duel, get_duel, remove_duel) ...

# Далее идут хэндлеры, уже с правильным порядком (dp создан до них)

@dp.callback_query(lambda c: c.data.startswith(("accept_duel_", "decline_duel_")))
async def duel_accept_decline(callback: CallbackQuery):
    # ... (содержимое без изменений)
    pass

@dp.callback_query(lambda c: c.data.startswith("duel_choice_"))
async def process_duel_choice(callback: CallbackQuery):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.reply_to_message and m.text and m.text.lower().strip() == "дуэль")
async def duel_by_reply(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.text and m.text.lower().startswith("дуэль ") and len(m.text.split()) >= 2)
async def duel_by_username(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.text and m.text.strip().lower() in ("хаммам", "хамам"))
async def hamam_cmd(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.text and m.text.lower() in ("турецкая баня", "турецкая"))
async def turkish_cmd(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.text and m.text.lower() in ("уменьшить кулдаун", "купить буст", "скидка кулдауна"))
async def reduce_cooldown_cmd(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.text and m.text.lower() in ("профиль", "мой профиль"))
async def profile_cmd(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.text and m.text.lower() in ("купить вип", "вип", "купитьвип"))
async def buy_vip_cmd(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.text and m.text.lower() in ("топ", "лидеры", "рейтинг"))
async def top_cmd(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.text and m.text.lower() in ("инфо", "помощь", "хамам бот"))
async def info_cmd(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.from_user.id == OWNER_ID and m.text and m.text.lower().startswith(("дать коины", "+коины", "накрутить коины")))
async def admin_add_coins(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.from_user.id == OWNER_ID and m.text and m.text.lower().startswith(("дать бурмалдатики", "+бурмалда", "накрутить бурмалда")))
async def admin_add_burmalda(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message(lambda m: m.text and m.text.lower().strip() in actions)
async def rp_action(message: Message):
    # ... (содержимое без изменений)
    pass

@dp.message()
async def ignore(message: Message):
    pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
