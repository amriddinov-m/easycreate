from aiogram import F, types

from clientbot.data.callback_datas import OrderHistoryCallbackData
from clientbot import shortcuts, strings
from clientbot.keyboards import inline_kb
from config import settings
from loader import client_bot_router


def order_id_handler(message: types.Message):
    if message.text and message.text.startswith("/order_"):
        #await message.answer("here")
        parts = message.text.split("_")
        if len(parts) == 2:
            order_id = parts[1]
            if order_id.isdigit():
                return True

@client_bot_router.callback_query(OrderHistoryCallbackData.filter())
async def order_history_cd(query: types.CallbackQuery, callback_data: OrderHistoryCallbackData):
    match callback_data.action:
        case "paginate":
            orders, count = await shortcuts.get_order_history(query.from_user.id, page=callback_data.page)
            text = await strings.print_order_history(orders)
            await query.message.edit_text(text, reply_markup=inline_kb.order_history_kb(count, callback_data.page))
        case "page-list":
            orders, count = await shortcuts.get_order_history(query.from_user.id, page=callback_data.page)
            text = "📖 Пожалуйста, выберите страницу"
            await query.message.edit_text(text, reply_markup=inline_kb.order_history_pages(count, callback_data.page))
    await query.answer()
