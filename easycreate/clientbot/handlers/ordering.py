from contextlib import suppress

from aiogram import types, flags
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from clientbot import shortcuts, strings
from clientbot.data.callback_datas import (
    CountryCallbackData,
    OperatorCallbackData,
    OrderCallbackData,
    ProductCallbackData
)
from clientbot.data.states import CountryState, ProductState
from clientbot.keyboards import inline_kb
from db.items import OrderNumberResponse

from loader import client_bot_router

@client_bot_router.callback_query(CountryCallbackData.filter())
@flags.rate_limit(key="choose-country")
async def choose_country(query: types.CallbackQuery, callback_data: CountryCallbackData, state: FSMContext):
    match callback_data.action:
        case "paginate":
            await state.clear()
            markup = await inline_kb.countries_kb(page=callback_data.page)
            with suppress(TelegramBadRequest):
                await query.message.edit_text(text="1. Выберете страну, номер телефона которой будет Вам выдан",
                                              reply_markup=markup)
        case "page-list":
            markup = await inline_kb.countries_pages_kb(callback_data.page)
            await query.message.edit_text(
                "📖 Пожалуйста, выберите страницу",
                reply_markup=markup
            )
        case "back":
            await query.message.edit_text(
                strings.WELCOME.format(name=query.from_user.first_name),
                reply_markup=inline_kb.main_menu()
            )
        case "retrieve":
            country = strings.COUNTRIES[callback_data.country_code]["name"]
            markup = await inline_kb.operators_kb(callback_data.country_code)
            await query.message.edit_text(
                f"🌍 Выбранная страна: {country}\n\n"
                "2. Выберите оператора номера",
                reply_markup=markup
            )
    await query.answer()


@client_bot_router.message(state=CountryState.search)
@flags.rate_limit(key="search_country")
async def search_country(message: types.Message, state: FSMContext):
    search_key = message.text
    countries = await shortcuts.get_countries(search_key=search_key)
    markup = inline_kb.country_search_result(countries)
    await message.answer(text=f"🔍 Результаты поиска ({len(countries)}):", reply_markup=markup)
    await state.clear()


@client_bot_router.callback_query(OperatorCallbackData.filter())
@flags.rate_limit(key="choose-operator")
async def choose_operator(query: types.CallbackQuery, callback_data: OperatorCallbackData):
    operator = callback_data.operator
    country = strings.COUNTRIES[callback_data.country_code]["name"]
    try:
        markup = await inline_kb.products_kb(callback_data.country_code, callback_data.operator)
    except Exception as e:
        await query.answer(e.args[0], show_alert=True)
    text = (f"🌍 Выбранная страна: {country}\n"
            f"📱 Выбранный оператор: {operator}\n\n"
            "3. Выберите сервис, от которого вам необходимо принять СМС")
    await query.message.edit_text(text, reply_markup=markup)
    await query.answer()


@client_bot_router.callback_query(ProductCallbackData.filter())
@flags.rate_limit(key="product")
async def products_cd(query: types.CallbackQuery, callback_data: ProductCallbackData, state: FSMContext):
    operator = callback_data.operator
    country = strings.COUNTRIES[callback_data.country_code]["name"]
    match callback_data.action:
        case "paginate":
            await state.clear()
            markup = await inline_kb.products_kb(callback_data.country_code, callback_data.operator, page=callback_data.page)
            text = (f"🌍 Выбранная страна: { country }\n"
                    f"📱 Выбранный оператор: {operator}\n\n"
                    "3. Выберите сервис, от которого вам необходимо принять СМС")
            with suppress(TelegramBadRequest):
                await query.message.edit_text(text, reply_markup=markup)
            await query.answer()
        case "page-list":
            markup = await inline_kb.products_pages_kb(callback_data)
            await query.message.edit_text(
                "📖 Пожалуйста, выберите страницу",
                reply_markup=markup
            )
            await query.answer()
        case "search":
            text = "🔍 Введите название сервиса для поиска. Например: telegram"
            markup = inline_kb.back_kb(ProductCallbackData(action="paginate", country_code=callback_data.country_code,
                                                           operator=callback_data.operator,
                                                           page=callback_data.page).pack())
            await query.message.edit_text(text, reply_markup=markup)
            await state.set_state(ProductState.search)
            await state.update_data(country_code=callback_data.country_code,
                                    operator=callback_data.operator)
            await query.answer()
        case "retrieve":
            cost = await shortcuts.get_price(callback_data.country_code, callback_data.product)
            price, _, _ = await shortcuts.calculate_price(query.from_user.id, cost)
            service = strings.SERVICES[callback_data.product]["name"]
            text = (f"▫️ Выбранный сервис: { service }\n"
                    f"▫️ Выбранный оператор: { operator }\n"
                    f"▫️ Выбранная страна: { country }\n\n"
                    f"▫️ Цена: {price}₽")
            await query.message.edit_text(text, 
                    reply_markup=inline_kb.buy_product_kb(callback_data.country_code, callback_data.operator, callback_data.product
            ))
        case "buy":
            cost = await shortcuts.get_price(callback_data.country_code, callback_data.product)
            price, profit, bot_admin_profit = await shortcuts.calculate_price(query.from_user.id, cost)
            user = await shortcuts.get_user(query.from_user.id)
            if user.balance < price:
                await query.answer("У вас недостаточно средств для покупки", show_alert=True)
            else:
                order = await shortcuts.get_phone(user.uid, callback_data.country_code, callback_data.product, callback_data.operator)
                if order == None:
                    await query.answer("Нет свободных номеров!", show_alert=True)
                else:
                    await shortcuts.change_balance(user.uid, -price, "buy", callback_data.product)
                    await shortcuts.create_order(
                        order_id=order.order_id, user=user, calculated_price=price, profit=profit, 
                        bot_admin_profit=0, country=country, country_code=callback_data.country_code,
                        operator=callback_data.operator, product=callback_data.product, 
                        phone=order.phone, price=price
                    )
                    await query.message.answer(f"Номер успешно заказан!\r\nВаш номер телефона: <code>{order.phone}</code>",
                                               reply_markup=inline_kb.order_actions(order.order_id))
                    
@client_bot_router.callback_query(OrderCallbackData.filter())
@flags.rate_limit(key="product")
async def products_cd(query: types.CallbackQuery, callback_data: OrderCallbackData, state: FSMContext):
    order = await shortcuts.get_order(callback_data.order_id)
    user = await shortcuts.get_user(query.from_user.id)
    match callback_data.action:
        case "check":
            result = await shortcuts.check_order(callback_data.order_id)
            if result == None:
                user.balance += order.price
                await user.save()
                await query.message.answer(f"Произошла проблема. Было возвращено {order.price} руб.\r\nПопробуйте сменить номер")
                await shortcuts.delete_order(callback_data.order_id)
                await query.message.delete(callback_data.order_id)
                await shortcuts.cancel_order_and_finish(callback_data.order_id)
            elif result == "wait":
                await query.answer("Код еще не доступен, попробуйте чуть позже", show_alert=True)
            else:
                await query.message.answer(f"Код: {result}")
                await shortcuts.change_order_details(callback_data.order_id, f"{result}", "received")
                await query.message.delete()
                await shortcuts.finish_order(callback_data.order_id)
        case "change":
            await shortcuts.cancel_order(callback_data.order_id)
            new_order: OrderNumberResponse = await shortcuts.get_phone(user.id, order.country_code, order.product, order.operator)
            if new_order == None:
                await query.answer("Нет свободных номеров! Подождите немного, пока освободятся", show_alert=True)
            else:
                await shortcuts.change_order_phone(callback_data.order_id, new_order.order_id, new_order.phone)
                await query.message.edit_text(f"Номер изменен!\r\nВаш номер телефона: <code>{new_order.phone}</code>",
                                              reply_markup=inline_kb.order_actions(new_order.order_id))
        case "cancel":
            await shortcuts.cancel_order_and_finish(callback_data.order_id)
            await query.message.delete()
            await query.message.answer(f"Покупка отменена. Возвращено: {order.price} руб")
        case "ban":
            await shortcuts.cancel_order_and_finish(callback_data.order_id)
            await shortcuts.add_phone_to_ban(user.uid, order.phone, order.product)
            await query.message.delete()
            await query.message.answer(f"Номер добален в черный список.\r\nПокупка отменена. Возвращено: {order.price} руб")
        

@client_bot_router.message(state=ProductState.search)
@flags.rate_limit(key="search_product")
async def search_product(message: types.Message, state: FSMContext):
    search_key = message.text
    data = await state.get_data()
    country_code = data['country_code']
    operator = data['operator']
    products = await shortcuts.get_products(strings.get_country_name(country_code), operator, search_key=search_key)
    markup = inline_kb.product_search_result(products, country_code, operator)
    await message.answer(text=f"🔍 Результаты поиска ({len(products)}):", reply_markup=markup)
    await state.clear()
