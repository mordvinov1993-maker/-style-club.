import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from dotenv import load_dotenv

from database import (
    create_database,
    register_user,
    get_user,
    get_achievements,
    add_points,
    get_gifts,
    redeem_gift,
    spin_wheel
)

load_dotenv()
ADMIN_ID = 900544895

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👤 Мой профиль"),
            KeyboardButton(text="⭐ Мои баллы")
        ],
        [
            KeyboardButton(text="🏆 Достижения"),
            KeyboardButton(text="🎁 Подарки")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)
@dp.message(F.text == "/myid")
async def show_my_id(message: Message):
    await message.answer(
        f"Твой Telegram ID: {message.from_user.id}"
    )
@dp.message(CommandStart())
async def start(message: Message):

    create_database()

    register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    await message.answer(
    "👋 Добро пожаловать в STYLE CLUB!\n\n"
    "Твоя регистрация прошла успешно.\n\n"
    "Здесь ты можешь зарабатывать баллы, "
    "открывать достижения и получать подарки.\n\n"
    "Добро пожаловать в клуб! 🎁",
    reply_markup=main_keyboard
)

@dp.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    user = get_user(message.from_user.id)

    if user:
        first_name, points = user

        await message.answer(
            f"👤 ТВОЙ ПРОФИЛЬ\n\n"
            f"Имя: {first_name}\n"
            f"⭐ Баланс: {points} баллов"
        )
    else:
        await message.answer("Профиль не найден. Нажми /start.")


@dp.message(F.text == "⭐ Мои баллы")
async def show_points(message: Message):
    user = get_user(message.from_user.id)

    if user:
        first_name, points = user

        await message.answer(
            f"⭐ ТВОИ БАЛЛЫ\n\n"
            f"Текущий баланс: {points} баллов\n\n"
            f"Баллы можно будет использовать для получения подарков!"
        )
    else:
        await message.answer("Сначала нажми /start для регистрации.")
@dp.message(F.text == "🎁 Подарки")
async def show_gifts(message: Message):
    gifts = get_gifts()

    if not gifts:
        await message.answer("Пока подарков нет.")
        return

    await message.answer("🎁 КАТАЛОГ ПОДАРКОВ\n")

    for gift_id, title, price in gifts:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"Обменять за {price} баллов",
                        callback_data=f"redeem:{gift_id}"
                    )
                ]
            ]
        )

        await message.answer(
            f"🎁 {title}\nСтоимость: {price} баллов",
            reply_markup=keyboard
        )
@dp.callback_query(F.data.startswith("redeem:"))
async def process_redeem(callback: CallbackQuery):
    gift_id = int(callback.data.split(":")[1])

    status, title = redeem_gift(
        callback.from_user.id,
        gift_id
    )

    if status == "success":
        await callback.message.answer(
            f"🎉 Поздравляем!\n\n"
            f"Ты обменял баллы на подарок: {title}."
        )

    elif status == "not_enough":
        user = get_user(callback.from_user.id)
        points = user[1] if user else 0

        await callback.message.answer(
            f"Недостаточно баллов для подарка «{title}».\n\n"
            f"Твой баланс: {points} баллов."
        )

    elif status == "not_found":
        await callback.message.answer("Этот подарок не найден.")

    elif status == "no_user":
        await callback.message.answer("Сначала нажми /start.")

    await callback.answer()        
@dp.message(F.text == "🏆 Достижения")
async def show_achievements(message: Message):
    achievements = get_achievements(message.from_user.id)

    if achievements:
        text = "🏆 ТВОИ ДОСТИЖЕНИЯ\n\n"

        for title, earned_at in achievements:
            text += f"⭐ {title}\n"

        await message.answer(text)
    else:
        await message.answer(
            "🏆 У тебя пока нет достижений.\n\n"
            "Выполняй задания и участвуй в жизни STYLE CLUB — "
            "здесь будут появляться твои награды!"
        )  
@dp.message(F.text.startswith("/addpoints"))
async def admin_add_points(message: Message):

    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа к этой команде.")
        return

    try:
        parts = message.text.split()

        telegram_id = int(parts[1])
        points = int(parts[2])

        if points <= 0:
            await message.answer("Количество баллов должно быть больше нуля.")
            return

        add_points(telegram_id, points)

        await message.answer(
            f"✅ Начислено {points} баллов пользователю {telegram_id}."
        )

    except (IndexError, ValueError):
        await message.answer(
            "Используй команду так:\n\n"
            "/addpoints Telegram_ID количество"
        )         
async def main():
    print("STYLE CLUB запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())