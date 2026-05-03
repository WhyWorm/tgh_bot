import asyncio
import logging
import sqlite3
import html
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

BOT_TOKEN = "8644503362:AAEPogfQT9w91J3lErAaqeGqMUEjEthZcFU"
OWNER_ID = 5618715354

# Исправленная конфигурация логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # здесь %(name)s, а не %name)s
)
logger = logging.getLogger(__name__)

# Создаём бота и диспетчер ДО хэндлеров
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

# ---------- ФУНКЦИИ ПОЛЬЗОВАТЕЛЕЙ ----------
def get_user(user_id: int):
    conn = sqlite3.connect("hamam.db")
    c = conn.cursor()
    c.execute("SELECT level, coins, burmalda, vip_until, last_hamam, cooldown_bonus FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "level": row[0],
            "coins": row[1],
            "burmalda": row[2],
            "vip_until": row[3],
            "last_hamam": row[4],
            "cooldown_bonus": row[5]
        }
    return {"level": 1, "coins": 0, "burmalda": 0, "vip_until": None, "last_hamam": None, "cooldown_bonus": 0}

def save_user(user_id: int, **kwargs):
    conn = sqlite3.connect("hamam.db")
    c = conn.cursor()
    cur = get_user(user_id)
    level = kwargs.get('level', cur["level"])
    coins = kwargs.get('coins', cur["coins"])
    burmalda = kwargs.get('burmalda', cur["burmalda"])
    vip_until = kwargs.get('vip_until', cur["vip_until"])
    last_hamam = kwargs.get('last_hamam', cur["last_hamam"])
    cooldown_bonus = kwargs.get('cooldown_bonus', cur["cooldown_bonus"])
    c.execute('''
        INSERT OR REPLACE INTO users (user_id, level, coins, burmalda, vip_until, last_hamam, cooldown_bonus)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, level, coins, burmalda, vip_until, last_hamam, cooldown_bonus))
    conn.commit()
    conn.close()

def is_vip(user_id: int) -> bool:
    u = get_user(user_id)
    if u["vip_until"]:
        return datetime.fromisoformat(u["vip_until"]) > datetime.now()
    return False

def get_effective_cooldown(user_id: int) -> int:
    vip = is_vip(user_id)
    base = 15 if vip else 30
    bonus = get_user(user_id)["cooldown_bonus"]
    result = base - bonus
    return max(1, result)

def update_hamam(user_id: int) -> dict:
    user = get_user(user_id)
    now = datetime.now()
    cd_minutes = get_effective_cooldown(user_id)
    if user["last_hamam"]:
        last = datetime.fromisoformat(user["last_hamam"])
        if now - last < timedelta(minutes=cd_minutes):
            remaining = timedelta(minutes=cd_minutes) - (now - last)
            m, s = divmod(remaining.seconds, 60)
            return {
                "success": False,
                "message": f"❌ <b>Кулдаун {cd_minutes} мин.</b> Следующий раз через {m} мин {s} сек."
            }
    new_level = user["level"] + 1
    base_coins = 6
    coins_gained = base_coins * (2 if is_vip(user_id) else 1)
    new_coins = user["coins"] + coins_gained
    save_user(user_id, level=new_level, coins=new_coins, last_hamam=now.isoformat())
    funny = [
        "🧖 Пропарился как редиска!",
        "🫧 Пахнешь лавандой",
        "💨 Пшик! Хамам обнял",
        "🛁 Массажист сказал: Ты молодец",
        "🎉 Уровень повысился!",
        "🍃 Карма чище сауны",
        "🔥 Конкуренты выцвели",
        "💎 Камень силы сияет"
    ]
    return {
        "success": True,
        "level": new_level,
        "coins_gained": coins_gained,
        "total_coins": new_coins,
        "funny": random.choice(funny),
        "message": f"🛁 <b>Хамам принял тебя!</b>\n🏆 Уровень повышен до <b>{new_level}</b>\n💰 Ты получил <b>{coins_gained}</b> коинов.\n✨ Всего: <b>{new_coins}</b>"
    }

def update_turkish_bath(user_id: int) -> dict:
    user = get_user(user_id)
    now = datetime.now()
    conn = sqlite3.connect("hamam.db")
    c = conn.cursor()
    c.execute("SELECT last_turkish FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    last_turkish = row[0] if row else None
    if last_turkish:
        last = datetime.fromisoformat(last_turkish)
        if now - last < timedelta(minutes=5):
            remaining = timedelta(minutes=5) - (now - last)
            m, s = divmod(remaining.seconds, 60)
            conn.close()
            return {"success": False, "message": f"❌ Турецкая баня раз в 5 минут. Подожди {m} мин {s} сек."}
    gain = random.randint(1, 3)
    new_burmalda = user["burmalda"] + gain
    save_user(user_id, burmalda=new_burmalda)
    c.execute("UPDATE users SET last_turkish = ? WHERE user_id = ?", (now.isoformat(), user_id))
    conn.commit()
    conn.close()
    funny_turkish = [
        "🧖‍♂️ Пар турецкий – сила для бурмалдатиков!",
        "🫠 Ты получил бурмалдатик(а) из пара.",
        "💨 Горячий камень – +{gain} бурмалдатика!",
        "🛁 Хамам-турция благословляет тебя.",
        "🎁 С маслицем – аппетитные бурмалдатики!"
    ]
    chosen = random.choice(funny_turkish).replace("{gain}", str(gain))
    return {
        "success": True,
        "gain": gain,
        "total": new_burmalda,
        "message": f"🧼 <b>Турецкая баня!</b>\n{chosen}\nТы получил <b>{gain}</b> бурмалдатик(ов). Всего: <b>{new_burmalda}</b>."
    }

def reduce_cooldown(user_id: int, cost: int = 20) -> tuple:
    user = get_user(user_id)
    if user["burmalda"] < cost:
        return False, f"❌ Не хватает бурмалдатиков. Нужно {cost}, у тебя {user['burmalda']}.", None
    new_burmalda = user["burmalda"] - cost
    new_bonus = user["cooldown_bonus"] + 5
    save_user(user_id, burmalda=new_burmalda, cooldown_bonus=new_bonus)
    return True, f"✨ Ты потратил {cost} бурмалдатиков! Кулдаун хаммама уменьшен на 5 минут (теперь −{new_bonus} мин).", new_bonus

def add_coins_to_user(target_id: int, amount: int):
    user = get_user(target_id)
    new_coins = user["coins"] + amount
    save_user(target_id, coins=new_coins)
    return new_coins

def add_burmalda_to_user(target_id: int, amount: int):
    user = get_user(target_id)
    new_burmalda = user["burmalda"] + amount
    save_user(target_id, burmalda=new_burmalda)
    return new_burmalda

MELLSTROY_STICKERS = []
STICKER_CHANCE = 0.15

async def maybe_send_sticker(message: Message):
    if MELLSTROY_STICKERS and random.random() < STICKER_CHANCE:
        try:
            await message.reply_sticker(random.choice(MELLSTROY_STICKERS))
        except Exception as e:
            logger.warning(f"Стикер не отправился: {e}")

# ---------- ДУЭЛИ ----------
duel_choices = {}

def set_duel(challenger_id, opponent_id, chat_id, message_id):
    conn = sqlite3.connect("hamam.db")
    c = conn.cursor()
    c.execute("DELETE FROM duels WHERE challenger_id = ? OR opponent_id = ?", (challenger_id, opponent_id))
    c.execute("INSERT INTO duels (challenger_id, opponent_id, challenge_time, chat_id, message_id) VALUES (?, ?, ?, ?, ?)",
              (challenger_id, opponent_id, datetime.now().isoformat(), chat_id, message_id))
    conn.commit()
    conn.close()

def get_duel(user_id):
    conn = sqlite3.connect("hamam.db")
    c = conn.cursor()
    c.execute("SELECT challenger_id, opponent_id, chat_id, message_id FROM duels WHERE challenger_id = ? OR opponent_id = ?", (user_id, user_id))
    row = c.fetchone()
    conn.close()
    if row:
        return {"challenger": row[0], "opponent": row[1], "chat_id": row[2], "message_id": row[3]}
    return None

def remove_duel(challenger_id, opponent_id):
    conn = sqlite3.connect("hamam.db")
    c = conn.cursor()
    c.execute("DELETE FROM duels WHERE (challenger_id = ? AND opponent_id = ?) OR (challenger_id = ? AND opponent_id = ?)",
              (challenger_id, opponent_id, opponent_id, challenger_id))
    conn.commit()
    conn.close()

def get_duel_winner(challenger_choice, opponent_choice):
    if challenger_choice == opponent_choice:
        return 0
    if challenger_choice == 0 and opponent_choice == 1:
        return 1
    if challenger_choice == 1 and opponent_choice == 2:
        return 1
    if challenger_choice == 2 and opponent_choice == 0:
        return 1
    return 2

def get_choice_keyboard(challenger_id, opponent_id):
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton(text="🫧 Пена", callback_data=f"duel_choice_{challenger_id}_{opponent_id}_0"),
        InlineKeyboardButton(text="💆‍♂️ Массаж", callback_data=f"duel_choice_{challenger_id}_{opponent_id}_1"),
        InlineKeyboardButton(text="🌿 Веник", callback_data=f"duel_choice_{challenger_id}_{opponent_id}_2")
    )
    return keyboard

def get_accept_keyboard(challenger_id, opponent_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_duel_{challenger_id}_{opponent_id}"),
        InlineKeyboardButton(text="❌ Отказаться", callback_data=f"decline_duel_{challenger_id}_{opponent_id}")
    )
    return keyboard

async def duel_timeout(challenger_id, opponent_id, chat_id, message_id):
    await asyncio.sleep(120)
    duel = get_duel(challenger_id)
    if duel and duel["opponent"] == opponent_id and duel["challenger"] == challenger_id:
        key = (challenger_id, opponent_id)
        if key in duel_choices:
            c_choice = duel_choices[key]["challenger_choice"]
            o_choice = duel_choices[key]["opponent_choice"]
            if c_choice is None or o_choice is None:
                if c_choice is None:
                    loser_id = challenger_id
                    winner_id = opponent_id
                else:
                    loser_id = opponent_id
                    winner_id = challenger_id
                winner = await bot.get_chat(winner_id)
                loser = await bot.get_chat(loser_id)
                winner_lvl = get_user(winner.id)["level"] + 1
                winner_coins = get_user(winner.id)["coins"] + 3
                save_user(winner.id, level=winner_lvl, coins=winner_coins)
                loser_coins = max(0, get_user(loser.id)["coins"] - 1)
                save_user(loser.id, coins=loser_coins)
                text = (
                    f"⌛ <b>Время вышло!</b> {html.escape(loser.full_name)} не сделал выбор.\n"
                    f"👑 Побеждает {html.escape(winner.full_name)}!\n"
                    f"📈 +1 уровень, +3 коина → уровень {winner_lvl}, коинов {winner_coins}\n"
                    f"💔 {html.escape(loser.full_name)} теряет 1 коин → коинов {loser_coins}"
                )
                try:
                    await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, parse_mode="HTML")
                except:
                    await bot.send_message(chat_id, text, parse_mode="HTML")
                remove_duel(challenger_id, opponent_id)
                if key in duel_choices:
                    del duel_choices[key]

# ---------- ХЭНДЛЕРЫ ----------
@dp.callback_query(lambda c: c.data.startswith(("accept_duel_", "decline_duel_")))
async def duel_accept_decline(callback: CallbackQuery):
    data = callback.data
    parts = data.split('_')
    action = parts[0]
    challenger_id = int(parts[2])
    opponent_id = int(parts[3])
    user_id = callback.from_user.id
    if user_id != opponent_id:
        await callback.answer("Это не тебя вызывали!", show_alert=True)
        return
    duel = get_duel(user_id)
    if not duel or duel["challenger"] != challenger_id or duel["opponent"] != opponent_id:
        await callback.answer("Вызов уже обработан или устарел.", show_alert=True)
        return
    if action == "decline":
        remove_duel(challenger_id, opponent_id)
        await callback.message.edit_text(
            f"❌ {html.escape(callback.from_user.full_name)} отказался от дуэли.",
            parse_mode="HTML",
            reply_markup=None
        )
        await callback.answer("Ты отказался.")
        return
    # Accept
    challenger = await bot.get_chat(challenger_id)
    try:
        keyboard = get_choice_keyboard(challenger_id, opponent_id)
        await bot.send_message(opponent_id,
                               f"⚔️ Ты принял дуэль с {html.escape(challenger.full_name)}!\n"
                               f"Выбери своё действие (Пена, Массаж или Веник).\n"
                               f"У тебя есть 2 минуты.",
                               parse_mode="HTML",
                               reply_markup=keyboard)
        await bot.send_message(challenger_id,
                               f"⚔️ {html.escape(callback.from_user.full_name)} принял дуэль!\n"
                               f"Теперь выбери действие в личных сообщениях бота (кнопки появятся).",
                               parse_mode="HTML")
        keyboard_challenger = get_choice_keyboard(challenger_id, opponent_id)
        await bot.send_message(challenger_id,
                               f"Выбери действие (Пена, Массаж, Веник):",
                               parse_mode="HTML",
                               reply_markup=keyboard_challenger)
        await callback.message.edit_text(
            f"⚔️ Дуэль между {html.escape(challenger.full_name)} и {html.escape(callback.from_user.full_name)} началась!\n"
            f"Оба участника получили выбор в личные сообщения. У них 2 минуты.",
            parse_mode="HTML",
            reply_markup=None
        )
        asyncio.create_task(duel_timeout(challenger_id, opponent_id, duel["chat_id"], duel["message_id"]))
        await callback.answer("Дуэль принята!")
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Не удалось отправить сообщение участникам. Возможно, кто-то не начал диалог с ботом.",
            parse_mode="HTML"
        )
        remove_duel(challenger_id, opponent_id)
        await callback.answer("Ошибка: напишите боту /start в личку.")

@dp.callback_query(lambda c: c.data.startswith("duel_choice_"))
async def process_duel_choice(callback: CallbackQuery):
    data = callback.data
    parts = data.split('_')
    challenger_id = int(parts[2])
    opponent_id = int(parts[3])
    choice = int(parts[4])
    user_id = callback.from_user.id
    if user_id not in (challenger_id, opponent_id):
        await callback.answer("Это не твоя дуэль!", show_alert=True)
        return
    duel = get_duel(challenger_id)
    if not duel or duel["challenger"] != challenger_id or duel["opponent"] != opponent_id:
        await callback.answer("Дуэль уже завершена или устарела.", show_alert=True)
        return
    key = (challenger_id, opponent_id)
    if key not in duel_choices:
        duel_choices[key] = {"challenger_choice": None, "opponent_choice": None}
    if user_id == challenger_id:
        if duel_choices[key]["challenger_choice"] is not None:
            await callback.answer("Ты уже сделал выбор!", show_alert=True)
            return
        duel_choices[key]["challenger_choice"] = choice
    else:
        if duel_choices[key]["opponent_choice"] is not None:
            await callback.answer("Ты уже сделал выбор!", show_alert=True)
            return
        duel_choices[key]["opponent_choice"] = choice
    await callback.answer("Выбор принят! Ожидаем второго игрока.")
    if duel_choices[key]["challenger_choice"] is not None and duel_choices[key]["opponent_choice"] is not None:
        c_choice = duel_choices[key]["challenger_choice"]
        o_choice = duel_choices[key]["opponent_choice"]
        result = get_duel_winner(c_choice, o_choice)
        chat_id = duel["chat_id"]
        orig_message_id = duel["message_id"]
        challenger = await bot.get_chat(challenger_id)
        opponent = await bot.get_chat(opponent_id)
        if result == 0:
            c_coins = get_user(challenger_id)["coins"] + 1
            o_coins = get_user(opponent_id)["coins"] + 1
            save_user(challenger_id, coins=c_coins)
            save_user(opponent_id, coins=o_coins)
            text = (
                f"⚔️ <b>Хамамная дуэль!</b>\n"
                f"🤝 Ничья! Оба выбрали одинаковое действие.\n"
                f"💰 Каждый получает по +1 коину.\n"
                f"{html.escape(challenger.full_name)}: {c_coins} коинов\n"
                f"{html.escape(opponent.full_name)}: {o_coins} коинов"
            )
        else:
            winner_id = challenger_id if result == 1 else opponent_id
            loser_id = opponent_id if result == 1 else challenger_id
            winner = await bot.get_chat(winner_id)
            loser = await bot.get_chat(loser_id)
            winner_lvl = get_user(winner.id)["level"] + 1
            winner_coins = get_user(winner.id)["coins"] + 5
            loser_lvl = max(1, get_user(loser.id)["level"] - 1)
            loser_coins = max(0, get_user(loser.id)["coins"] - 2)
            save_user(winner.id, level=winner_lvl, coins=winner_coins)
            save_user(loser.id, level=loser_lvl, coins=loser_coins)
            text = (
                f"⚔️ <b>Хамамная дуэль!</b>\n"
                f"👑 <b>{html.escape(winner.full_name)}</b> победил!\n"
                f"📈 +1 уровень, +5 коинов → уровень {winner_lvl}, коинов {winner_coins}\n"
                f"💔 <b>{html.escape(loser.full_name)}</b> проиграл: -1 уровень, -2 коина → уровень {loser_lvl}, коинов {loser_coins}"
            )
        try:
            await bot.edit_message_text(text, chat_id=chat_id, message_id=orig_message_id, parse_mode="HTML")
        except:
            await bot.send_message(chat_id, text, parse_mode="HTML")
        remove_duel(challenger_id, opponent_id)
        del duel_choices[key]
        await bot.send_message(challenger_id, "Дуэль завершена! Результат в группе.")
        await bot.send_message(opponent_id, "Дуэль завершена! Результат в группе.")
        await maybe_send_sticker(callback.message)

@dp.message(lambda m: m.reply_to_message and m.text and m.text.lower().strip() == "дуэль")
async def duel_by_reply(message: Message):
    challenger = message.from_user
    opponent = message.reply_to_message.from_user
    if challenger.id == opponent.id:
        await message.reply("❌ Нельзя вызвать на дуэль самого себя.")
        return
    keyboard = get_accept_keyboard(challenger.id, opponent.id)
    sent = await message.reply(
        f"⚔️ <b>{html.escape(challenger.full_name)} вызывает на дуэль {html.escape(opponent.full_name)}!</b>\n"
        f"У {html.escape(opponent.full_name)} есть 2 минуты, чтобы принять или отказаться.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    set_duel(challenger.id, opponent.id, message.chat.id, sent.message_id)
    await asyncio.sleep(120)
    duel = get_duel(challenger.id)
    if duel and duel["challenger"] == challenger.id and duel["opponent"] == opponent.id:
        remove_duel(challenger.id, opponent.id)
        await sent.edit_text("⌛ Вызов устарел: противник не ответил.", reply_markup=None)

@dp.message(lambda m: m.text and m.text.lower().startswith("дуэль ") and len(m.text.split()) >= 2)
async def duel_by_username(message: Message):
    challenger = message.from_user
    parts = message.text.split()
    target_text = parts[1].strip().lstrip('@')
    opponent = None
    try:
        chat = await bot.get_chat(target_text)
        opponent = chat.user or chat
    except:
        if target_text.isdigit():
            try:
                chat = await bot.get_chat(int(target_text))
                opponent = chat.user or chat
            except:
                pass
    if opponent is None:
        await message.reply("❌ Не найден пользователь. Убедись, что username правильный, или вызови дуэль ответом на сообщение.")
        return
    if challenger.id == opponent.id:
        await message.reply("❌ Нельзя вызвать на дуэль самого себя.")
        return
    keyboard = get_accept_keyboard(challenger.id, opponent.id)
    sent = await message.reply(
        f"⚔️ <b>{html.escape(challenger.full_name)} вызывает на дуэль {html.escape(opponent.full_name)}!</b>\n"
        f"У {html.escape(opponent.full_name)} есть 2 минуты, чтобы принять или отказаться.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    set_duel(challenger.id, opponent.id, message.chat.id, sent.message_id)
    await asyncio.sleep(120)
    duel = get_duel(challenger.id)
    if duel and duel["challenger"] == challenger.id and duel["opponent"] == opponent.id:
        remove_duel(challenger.id, opponent.id)
        await sent.edit_text("⌛ Вызов устарел: противник не ответил.", reply_markup=None)

@dp.message(lambda m: m.text and m.text.strip().lower() in ("хаммам", "хамам"))
async def hamam_cmd(message: Message):
    res = update_hamam(message.from_user.id)
    msg = res["message"] if not res["success"] else f"🧼 {res['funny']}\n{res['message']}"
    await message.reply(msg, parse_mode="HTML")
    await maybe_send_sticker(message)

@dp.message(lambda m: m.text and m.text.lower() in ("турецкая баня", "турецкая"))
async def turkish_cmd(message: Message):
    res = update_turkish_bath(message.from_user.id)
    await message.reply(res["message"], parse_mode="HTML")
    await maybe_send_sticker(message)

@dp.message(lambda m: m.text and m.text.lower() in ("уменьшить кулдаун", "купить буст", "скидка кулдауна"))
async def reduce_cooldown_cmd(message: Message):
    ok, msg, _ = reduce_cooldown(message.from_user.id)
    await message.reply(msg, parse_mode="HTML")
    if ok:
        await maybe_send_sticker(message)

@dp.message(lambda m: m.text and m.text.lower() in ("профиль", "мой профиль"))
async def profile_cmd(message: Message):
    u = get_user(message.from_user.id)
    vip = is_vip(message.from_user.id)
    cd = get_effective_cooldown(message.from_user.id)
    text = f"📊 <b>Твой хамам-профиль</b>\n🏆 Уровень: {u['level']}\n💰 Коины: {u['coins']}\n🍥 Бурмалдатики: {u['burmalda']}\n"
    if vip:
        until = datetime.fromisoformat(u['vip_until'])
        text += f"👑 VIP до {until.strftime('%d.%m.%Y %H:%M')}\n"
    else:
        text += "🤴 VIP не активен. Напиши «купить вип» (100 коинов)\n"
    text += f"⏱️ Кулдаун хаммама: {cd} мин (базовый {'15' if vip else '30'} - бонус {u['cooldown_bonus']})\n"
    if u['last_hamam']:
        last = datetime.fromisoformat(u['last_hamam'])
        text += f"🕒 Последний визит: {last.strftime('%d.%m.%Y %H:%M:%S')}"
    else:
        text += "🕒 Первый раз? Напиши «хаммам»."
    await message.reply(text, parse_mode="HTML")

@dp.message(lambda m: m.text and m.text.lower() in ("купить вип", "вип", "купитьвип"))
async def buy_vip_cmd(message: Message):
    u = get_user(message.from_user.id)
    if u["coins"] >= 100:
        new_coins = u["coins"] - 100
        vip_until = (datetime.now() + timedelta(days=7)).isoformat()
        save_user(message.from_user.id, coins=new_coins, vip_until=vip_until)
        msg = f"✨ <b>Ты купил VIP на 7 дней!</b> Двойные коины, кулдаун 15 минут (до бонусов)."
    else:
        msg = f"❌ Недостаточно коинов. Нужно 100, у тебя {u['coins']}."
    await message.reply(msg, parse_mode="HTML")

@dp.message(lambda m: m.text and m.text.lower() in ("топ", "лидеры", "рейтинг"))
async def top_cmd(message: Message):
    conn = sqlite3.connect("hamam.db")
    c = conn.cursor()
    c.execute("SELECT user_id, level, coins FROM users ORDER BY level DESC, coins DESC LIMIT 10")
    top = c.fetchall()
    conn.close()
    if not top:
        await message.reply("🏆 Пусто. Напиши «хаммам» и стань первым!")
        return
    text = "🏆 <b>Топ-10 хамам-мастеров</b>\n\n"
    for i, (uid, lvl, coins) in enumerate(top, 1):
        try:
            u = await bot.get_chat(uid)
            name = u.full_name
        except:
            name = f"Пользователь {uid}"
        text += f"{i}. {html.escape(name)} — уровень {lvl} (⚡{coins} коинов)\n"
    await message.reply(text, parse_mode="HTML")

@dp.message(lambda m: m.text and m.text.lower() in ("инфо", "помощь", "хамам бот"))
async def info_cmd(message: Message):
    await message.answer(
        "🧼 <b>Хамам-бот | Дуэли в ЛС с выбором предмета</b>\n\n"
        "🎮 <b>Основное:</b>\n"
        "«хаммам» – повысить уровень, получить коины\n"
        "«турецкая баня» – бурмалдатики\n"
        "«уменьшить кулдаун» – тратить булки\n"
        "«купить вип» – 100 коинов\n"
        "«профиль» – статистика\n"
        "«топ» – рейтинг\n\n"
        "⚔️ <b>Дуэль:</b>\n"
        "• Ответь на сообщение человека и напиши «дуэль» – вызовешь его\n"
        "• Или напиши «дуэль @username»\n"
        "• В чате появятся кнопки «Принять» / «Отказаться»\n"
        "• После принятия оба участника получают в ЛС кнопки: Пена, Массаж, Веник\n"
        "• У каждого 2 минуты на выбор. Победитель получает +1 уровень, +5 коинов, проигравший – -1 уровень, -2 коина.\n"
        "• Если кто-то не выбрал – он проигрывает, победитель получает +1 уровень, +3 коина.\n\n"
        "🔥 <b>Ролевые действия (ответом):</b>\n"
        "подрочить, обнять, поцеловать, ударить, погладить, укусить, пнуть, облизать, ущипнуть, придушить, изнасиловать, трахнуть, развратить",
        parse_mode="HTML"
    )

@dp.message(lambda m: m.from_user.id == OWNER_ID and m.text and m.text.lower().startswith(("дать коины", "+коины", "накрутить коины")))
async def admin_add_coins(message: Message):
    try:
        parts = message.text.split()
        amount = None
        target = None
        if message.reply_to_message:
            target = message.reply_to_message.from_user
            for p in parts:
                if p.isdigit():
                    amount = int(p)
                    break
        else:
            for p in parts:
                if p.startswith('@'):
                    try:
                        target = await bot.get_chat(p[1:])
                        target = target.user
                    except:
                        pass
                elif p.isdigit():
                    amount = int(p)
            if not target and len(parts) >= 2:
                try:
                    uid = int(parts[1])
                    target = await bot.get_chat(uid)
                    target = target.user
                except:
                    pass
        if not target or amount is None:
            await message.reply("❌ Используй: дать коины @username 100 (или ответом на сообщение).")
            return
        new_coins = add_coins_to_user(target.id, amount)
        await message.reply(f"✅ Добавлено {amount} коинов пользователю {html.escape(target.full_name)}. Теперь у него {new_coins} коинов.", parse_mode="HTML")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

@dp.message(lambda m: m.from_user.id == OWNER_ID and m.text and m.text.lower().startswith(("дать бурмалдатики", "+бурмалда", "накрутить бурмалда")))
async def admin_add_burmalda(message: Message):
    try:
        parts = message.text.split()
        amount = None
        target = None
        if message.reply_to_message:
            target = message.reply_to_message.from_user
            for p in parts:
                if p.isdigit():
                    amount = int(p)
                    break
        else:
            for p in parts:
                if p.startswith('@'):
                    try:
                        target = await bot.get_chat(p[1:])
                        target = target.user
                    except:
                        pass
                elif p.isdigit():
                    amount = int(p)
        if not target or amount is None:
            await message.reply("❌ Используй: дать бурмалдатики @username 50")
            return
        new_b = add_burmalda_to_user(target.id, amount)
        await message.reply(f"✅ Добавлено {amount} бурмалдатиков пользователю {html.escape(target.full_name)}. Теперь у него {new_b} бурмалдатиков.", parse_mode="HTML")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

actions = {
    "подрочить": ("💦", "сладко подрочил"),
    "обнять": ("🤗", "нежно обнял"),
    "поцеловать": ("😘", "горячо поцеловал"),
    "ударить": ("👊", "со всей дури ударил"),
    "погладить": ("🖐️", "ласково погладил"),
    "укусить": ("🦷", "больно укусил"),
    "пнуть": ("🦶", "сильно пнул"),
    "облизать": ("👅", "чувственно облизал"),
    "ущипнуть": ("✨", "больно ущипнул"),
    "придушить": ("😤", "слегка придушил"),
    "изнасиловать": ("🔞", "жестоко изнасиловал"),
    "трахнуть": ("🍆💦", "грубо трахнул"),
    "развратить": ("😈", "развратил")
}

@dp.message(lambda m: m.text and m.text.lower().strip() in actions)
async def rp_action(message: Message):
    action = message.text.lower().strip()
    emoji, phrase = actions[action]
    reply = message.reply_to_message
    if not reply:
        await message.reply("❌ Ответь на сообщение того, кого хочешь трогать.", parse_mode="HTML")
        return
    actor = message.from_user
    target = reply.from_user
    actor_name = f"@{actor.username}" if actor.username else actor.first_name
    target_name = f"@{target.username}" if target.username else target.first_name
    if actor.id == target.id:
        txt = f"{emoji} | <b>{html.escape(actor_name)} {html.escape(phrase)} сам(а) себя</b>"
    else:
        txt = f"{emoji} | <b>{html.escape(actor_name)} {html.escape(phrase)} {html.escape(target_name)}</b>"
    await message.reply(txt, parse_mode="HTML")
    await maybe_send_sticker(message)

@dp.message()
async def ignore(message: Message):
    pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
