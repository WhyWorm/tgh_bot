import asyncio
import json
import random
import time
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "ТВОЙ_ТОКЕН_ЗДЕСЬ"

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

DB_FILE = "players.json"
COOLDOWN = 300

# --- База ---
def load_data():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

players = load_data()

def get_player(user_id):
    user_id = str(user_id)
    if user_id not in players:
        players[user_id] = {
            "coins": 0,
            "last_hammam": 0,
            "wins": 0,
            "xp": 0,
            "level": 1
        }
    return players[user_id]

# --- Уровни ---
def add_xp(player, amount):
    player["xp"] += amount
    need = player["level"] * 10

    if player["xp"] >= need:
        player["xp"] -= need
        player["level"] += 1
        return True
    return False

# --- Кнопки ---
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧖 Хаммам")],
        [KeyboardButton(text="⚔️ Дуэль")],
        [KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="👤 Профиль")]
    ],
    resize_keyboard=True
)

# ▶️ Основной обработчик
@dp.message()
async def main_handler(message: Message):
    text = message.text.lower()
    player = get_player(message.from_user.id)

    name = message.from_user.first_name

    # --- ХАММАМ ---
    if "хаммам" in text:
        now = time.time()

        if now - player["last_hammam"] < COOLDOWN:
            remaining = int(COOLDOWN - (now - player["last_hammam"]))
            await message.answer(
                f"⏳ <b>Подожди немного</b>\n"
                f"До следующего хаммама: <code>{remaining} сек</code>",
                reply_markup=kb
            )
            return

        player["last_hammam"] = now

        coins = 4 + player["level"]
        player["coins"] += coins

        leveled = add_xp(player, 3)

        msg = (
            f"🧖 <b>Хаммам</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 {name}\n"
            f"💰 Получено: <b>+{coins}</b>\n"
            f"💳 Баланс: <code>{player['coins']}</code>"
        )

        if leveled:
            msg += f"\n\n🎉 <b>Новый уровень!</b> → <code>{player['level']}</code>"

        save_data(players)
        await message.answer(msg, reply_markup=kb)

    # --- ДУЭЛЬ ---
    elif "дуэль" in text:
        if not message.reply_to_message:
            await message.answer(
                "❌ <b>Ошибка</b>\nОтветь на сообщение игрока для дуэли",
                reply_markup=kb
            )
            return

        user1 = str(message.from_user.id)
        user2 = str(message.reply_to_message.from_user.id)

        name1 = message.from_user.first_name
        name2 = message.reply_to_message.from_user.first_name

        if user1 == user2:
            await message.answer(
                "❌ <b>Нельзя драться с собой</b>",
                reply_markup=kb
            )
            return

        p1 = get_player(user1)
        p2 = get_player(user2)

        if p1["coins"] < 1 or p2["coins"] < 1:
            await message.answer(
                "❌ <b>Недостаточно коинов</b>",
                reply_markup=kb
            )
            return

        chance1 = p1["level"] + random.randint(1, 6)
        chance2 = p2["level"] + random.randint(1, 6)

        if chance1 > chance2:
            winner, loser = name1, name2
            players[user1]["coins"] += 2
            players[user2]["coins"] -= 1
            players[user1]["wins"] += 1
            add_xp(players[user1], 5)
        else:
            winner, loser = name2, name1
            players[user2]["coins"] += 2
            players[user1]["coins"] -= 1
            players[user2]["wins"] += 1
            add_xp(players[user2], 5)

        save_data(players)

        await message.answer(
            f"⚔️ <b>ДУЭЛЬ</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🥊 {name1} vs {name2}\n\n"
            f"🏆 Победитель: <b>{winner}</b>\n"
            f"💰 Награда: <code>+2</code>",
            reply_markup=kb
        )

    # --- ТОП ---
    elif "топ" in text:
        sorted_players = sorted(players.items(), key=lambda x: x[1]["coins"], reverse=True)

        msg = "🏆 <b>ТОП МАСТЕРОВ ХАММАМА</b>\n━━━━━━━━━━━━━━━\n"

        for i, (uid, data) in enumerate(sorted_players[:10], start=1):
            msg += f"{i}. <code>{uid}</code> — {data['coins']}💰 | lvl {data['level']}\n"

        await message.answer(msg, reply_markup=kb)

    # --- ПРОФИЛЬ ---
    elif "профиль" in text:
        await message.answer(
            f"👤 <b>ПРОФИЛЬ</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 Коины: <code>{player['coins']}</code>\n"
            f"📊 Уровень: <b>{player['level']}</b>\n"
            f"✨ XP: <code>{player['xp']}/{player['level']*10}</code>\n"
            f"⚔️ Победы: <code>{player['wins']}</code>",
            reply_markup=kb
        )

    else:
        await message.answer(
            "👇 <b>Выбери действие</b>",
            reply_markup=kb
        )

# ▶️ Запуск
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
