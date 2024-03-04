from contextlib import suppress

from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from loader import main_bot_router
from mainbot.keyboards import reply_kb


@main_bot_router.callback_query_handler(text="cancel", state="*")
async def cancel(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass
    await state.clear()


@main_bot_router.message(commands=['cancel'], state="*")
@main_bot_router.message(text="Отмена", state="*")
async def cancel_state(message: types.Message, state: FSMContext):
    with suppress(TelegramBadRequest):
        await message.answer(
            text="Отменено",
            reply_markup=reply_kb.main_menu()
        )
    await state.clear()
