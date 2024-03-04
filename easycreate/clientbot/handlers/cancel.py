from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramNotFound

from clientbot import strings
from clientbot.keyboards import reply_kb
from loader import client_bot_router


@client_bot_router.message(commands="cancel")
@client_bot_router.message(text=strings.CANCEL)
async def cancel_state(message: types.Message, state: FSMContext):
    await message.answer(strings.MAIN_MENU, reply_markup=reply_kb.main_menu())
    await state.clear()


@client_bot_router.callback_query_handler(text="cancel", state="*")
async def cancel(c: types.CallbackQuery, state: FSMContext):
    try:
        await c.message.delete()
    except (TelegramBadRequest, TelegramNotFound):
        await c.message.edit_reply_markup()
    await state.clear()
