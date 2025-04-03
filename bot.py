# bot.py

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from gpt import ask_gpt
from db import *
from aiogram.client.default import DefaultBotProperties
from utils import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import BotCommandScopeDefault

from aiogram.fsm.state import StatesGroup, State

class Onboarding(StatesGroup):
    language = State()
    name = State()
    age = State()
    sex = State()
    country = State()


user_sessions = {}  # key: user_id, value: session_id


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

async def main():
    await init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)



@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    full_name = message.from_user.full_name


    await add_user(user_id, full_name)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
                InlineKeyboardButton(text="🇰🇬 Кыргызча", callback_data="lang:kg"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")
            ]
        ]
    )

    await message.answer(extract_translations("lang.choose", lang="ru"), reply_markup=keyboard)
    await state.set_state(Onboarding.language)

    

@dp.callback_query(F.data.startswith("lang:"))
async def set_language(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split(":")[1]
    user_id = callback.from_user.id

    await update_user_field(user_id, "language", lang)


    await bot.set_my_commands(get_bot_commands(lang), scope=BotCommandScopeDefault())

    # Check FSM state — if we're in onboarding, continue
    current_state = await state.get_state()
    if current_state == Onboarding.language:
        await callback.message.answer(extract_translations("start.welcome", lang))
        await callback.message.answer(extract_translations("survey.ask_name", lang))
        await state.set_state(Onboarding.name)
    else:
        await callback.message.answer(extract_translations("lang.changed", lang))
        await state.clear()



@dp.message(Onboarding.name)
async def get_name(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    await update_user_field(message.from_user.id, "full_name", message.text)
    await message.answer(f"{extract_translations('greetings.nice_to_meet_you', lang)}, {message.text}!")
    await message.answer(extract_translations("survey.ask_age", lang))
    await state.set_state(Onboarding.age)

    
@dp.message(Onboarding.age)
async def get_age(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    await update_user_field(message.from_user.id, "age", int(message.text))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=extract_translations("sex.female", lang), callback_data="sex:female"),
                InlineKeyboardButton(text=extract_translations("sex.male", lang), callback_data="sex:male")
            ],
            [
                InlineKeyboardButton(text=extract_translations("sex.unknown", lang), callback_data="sex:unknown")
            ]
        ]
    )

    await message.answer(extract_translations("survey.ask_sex", lang), reply_markup=keyboard)
    await state.set_state(Onboarding.sex)


@dp.callback_query(F.data.startswith("sex:"))
async def get_sex(callback: types.CallbackQuery, state: FSMContext):
    sex_value = callback.data.split(":")[1]
    lang = await get_user_lang(callback.from_user.id)

    await update_user_field(callback.from_user.id, "sex", sex_value)

    await callback.message.answer(extract_translations("survey.ask_country", lang))
    await state.set_state(Onboarding.country)


@dp.message(Onboarding.country)
async def get_country(message: Message, state: FSMContext):
    await update_user_field(message.from_user.id, "country", message.text)
    lang = await get_user_lang(message.from_user.id)
    await message.answer(extract_translations("done", lang))
    await state.clear()


@dp.message(F.text.startswith("/newsession"))
async def cmd_newsession(message: Message):
    user_id = message.from_user.id
    lang = await get_user_lang(message.from_user.id)

    args = message.text.split(maxsplit=1)
    session_name = args[1] if len(args) > 1 else extract_translations("session.untitled", lang)
    session_id = await create_session(user_id, session_name)
    user_sessions[user_id] = session_id

    text = extract_translations("session.started", lang).format(session_name=session_name)
    await message.answer(text)


@dp.message(F.text == "/sessions")
async def cmd_sessions(message: Message):
    user_id = message.from_user.id
    sessions = await get_sessions(user_id)
    lang = await get_user_lang(message.from_user.id)
    if not sessions:
        await message.answer(extract_translations("sessions.empty", lang))
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"set_session:{session_id}")]
            for session_id, name, summary in sessions
        ]
    )

    await message.answer(extract_translations("sessions.list", lang), reply_markup=keyboard)


@dp.message(F.text == "/lang")
async def cmd_lang(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
                InlineKeyboardButton(text="🇰🇬 Кыргызча", callback_data="lang:kg"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")
            ]
        ]
    )
    await message.answer(extract_translations("lang.choose", lang), reply_markup=keyboard)
    await state.set_state(Onboarding.language)  # Reuse existing state


@dp.callback_query(F.data.startswith("set_session:"))
async def handle_set_session(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    remind_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=extract_translations("buttons.remind", lang), callback_data="remind_me")]
        ]
    )
    session_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    user_sessions[user_id] = session_id
    await callback.message.edit_text(extract_translations("session.activated_full", lang), reply_markup=remind_button)


@dp.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    session_id = user_sessions.get(user_id)
    lang = await get_user_lang(message.from_user.id)

    if not session_id:
        await message.answer(extract_translations("errors.no_active_sessions", lang), parse_mode=None)
        return

    user_input = message.text
    response = ask_gpt(user_input)

    await save_message(user_id, session_id, user_input, response)


    formatted = markdown_to_html(response)

    remind_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=extract_translations("buttons.remind", lang), callback_data="remind_me")]
        ]
    )

    await message.answer(formatted, reply_markup=remind_button)


@dp.callback_query(F.data == "remind_me")
async def handle_remind_me(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    session_id = user_sessions.get(user_id)
    lang = await get_user_lang(callback.from_user.id)

    if not session_id:
        await callback.message.answer(extract_translations("errors.no_active_sessions", lang))
        return

    history = await get_session_history(session_id, limit=10)

    if not history:
        await callback.message.answer(extract_translations("errors.no_messages", lang))
        return

    # Build conversation log for summarization
    conversation = ""
    for user_msg, bot_reply in history:
        conversation += f"User: {user_msg}\nAssistant: {bot_reply}\n"

    prompt = (
        "The assistant is being designed in Kyrgyzstan, so mostly the primarily used languages will be Russian and Kyrgyz. If you notice that the language is from turkic language family, then most likely it's Kyrgyz, so return the answers in Kyrgyz. Only if user specifies that it's Kazakh or some other turkic language, then you can continue the conversation in that language. This applies only towards turkic languages."
        "You are a helpful assistant that summarizes mental health conversations.\n"
        "Here is the session so far:\n\n"
        f"{conversation}\n\n"
        "Please provide a short, gentle, and clear summary to help the user remember what this session was about"
    )

    summary = ask_gpt(prompt)
    await callback.message.answer(
        f"🔁 <b>{extract_translations('session.summary', lang)}</b>:\n{markdown_to_html(summary)}"
    )





if __name__ == "__main__":
    asyncio.run(main())


