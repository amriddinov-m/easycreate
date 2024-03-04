import asyncio
import json
import re
from contextlib import suppress
from io import BytesIO
from pathlib import Path
from typing import Any, Union, Dict

import aiofiles
from aiogram import types, F, Bot, html
from aiogram.dispatcher.filters import BaseFilter
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramRetryAfter
)
from tortoise.exceptions import IntegrityError

from clientbot import shortcuts, strings
from clientbot.data.callback_datas import (
    AdminPanelCallbackData,
    BroadcastCallbackData,
    EditPercentCallbackData,
    MandatorySubscription
)
from clientbot.data.states import (
    BroadcastState,
    ChangePhoto,
    ChangeChannelLink,
    ChangeAdmin,
    ChangeSupport,
    Post,
    AddSubscriptionChat, ImportUsers
)
from clientbot.keyboards import inline_kb, reply_kb
from config import settings
from loader import client_bot_router
from utils.functions import get_call_method


class AdminFilter(BaseFilter):
    async def __call__(self, message: types.Message, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
        return message.from_user.id in [
            *settings.ADMIN_LIST,
            (await shortcuts.get_bot_owner()).uid
        ]


@client_bot_router.message(AdminFilter(), commands="admin")
async def enter_admin_panel(message: types.Message):
    await message.answer("Панель администратора", reply_markup=inline_kb.admin_buttons())


@client_bot_router.callback_query(AdminPanelCallbackData.filter())
async def admin_panel(query: types.CallbackQuery, callback_data: AdminPanelCallbackData, state: FSMContext):
    bot = await shortcuts.get_bot()
    uid = query.from_user.id
    if uid not in [*settings.ADMIN_LIST, bot.owner.uid]:
        await query.answer("Вы не админ", show_alert=True)
        await query.message.edit_reply_markup()
        return
    await query.answer()
    match callback_data.action:
        case "statistics":
            text = (f"Пользователей всего: {await shortcuts.get_all_users_count()}\n"
                    f"Новые пользователи: {await shortcuts.get_new_users_count()}\n"
                    f"Заработано всего: {await shortcuts.earned()}\n"
                    f"Прибыль(Сегодня): {await shortcuts.earned_today()}\n"
                    f"Заказов за сегодня: {await shortcuts.ordered_today()}\n")
            await query.message.edit_text(text, reply_markup=inline_kb.back_to_admin_panel())
        case "broadcast":
            try:
                await query.message.delete()
            except TelegramBadRequest:
                await query.message.edit_reply_markup()
            text = strings.BROADCAST.format(
                int(await shortcuts.get_all_users_count() * settings.SLEEP_TIME)
            )
            await query.message.answer(text=text, reply_markup=reply_kb.cancel())
            await state.set_state(BroadcastState.message)
        case "mandatory-subscription":
            chats = await shortcuts.get_subscription_chats(bot)
            text = strings.get_subscription_chats(bot.mandatory_subscription, chats)
            await query.message.edit_text(text, reply_markup=inline_kb.mandatory_subscription_status(
                bot.mandatory_subscription, len(chats)), disable_web_page_preview=True)
        case "change-photo":
            await query.message.edit_text("Отправьте фото чтобы изменить", reply_markup=inline_kb.admin_panel_cancel())
            await state.set_state(ChangePhoto.photo)
        case "channel-link":
            await query.message.edit_text("Отправьте ссылку на канал", reply_markup=inline_kb.admin_panel_cancel())
            await state.set_state(ChangeChannelLink.link)
        case "change-percent":
            await query.message.edit_text(
                f"Ваша процентная ставка: {bot.percent}%\n\n"
                f"Выберите процент для изменения:",
                reply_markup=inline_kb.percents()
            )
        case "change-admin":
            await state.set_state(ChangeAdmin.uid)
            await query.message.edit_text("Отправьте ИД нового администратора"
                                          "(Внимание! После введения ид этот человек "
                                          "автоматический станет владельцем этого бота)",
                                          reply_markup=inline_kb.admin_panel_cancel())
        case "change-support":
            await state.set_state(ChangeSupport.username_or_uid)
            await query.message.edit_text("Отправьте username или ИД новой поддержки",
                                          reply_markup=inline_kb.admin_panel_cancel())
        case "dump-users":
            await query.message.edit_text("Готовимся... Пожалуйста, подождите немного")
            users_ids = "\n".join(map(str, await shortcuts.get_users_ids(query.from_user.id))).encode("utf-8")
            with BytesIO() as file:
                file.write(users_ids)
                file.seek(0)
                await query.message.answer_document(types.BufferedInputFile(file.read(), "users.txt"))

        case "import-users":
            await query.answer("Скоро")
            # await query.message.edit_text("Отправьте файл, состоящий из идентификаторов пользователей, "
            #                               "каждый идентификатор пользователя в новой строке. "
            #                               "Лимит файла: 2.5МБ",
            #                               reply_markup=inline_kb.admin_panel_cancel())
            # await state.set_state(ImportUsers.file)

        case "cancel" | None:
            if callback_data.action == "cancel":
                await state.clear()
            await query.message.edit_text("Панель администратора", reply_markup=inline_kb.admin_buttons())


@client_bot_router.message(state=BroadcastState.message, content_types=settings.ALLOWED_CONTENT_TYPES)
async def broadcast_message(message: types.Message, state: FSMContext, bot: Bot):
    call = get_call_method(message)(message.from_user.id)
    await message.answer("Сообщение готово к отправке.", reply_markup=types.ReplyKeyboardRemove())
    call.reply_markup = inline_kb.post_buttons(call.reply_markup)
    await bot(call)
    await state.clear()


@client_bot_router.callback_query(BroadcastCallbackData.filter())
async def broadcast_confirmation(query: types.CallbackQuery, callback_data: BroadcastCallbackData, state: FSMContext):
    match callback_data.action:
        case "send":
            loop = asyncio.get_event_loop()
            bot = await shortcuts.get_bot()
            loop.create_task(broadcast_to_users(bot.token, query.message, query.from_user.id))
            try:
                await query.message.edit_text("Начался")
            except TelegramBadRequest:
                await query.message.answer("Начался")
        case "add-button":
            await query.answer()
            await query.message.answer("Отправьте кнопки. Например, [Перейти](https://t.me/DoSimplebot)",
                                       disable_web_page_preview=True,
                                       reply_markup=reply_kb.cancel())
            await state.set_state(Post.buttons)
            await state.update_data(
                markup=query.message.reply_markup.json(exclude_none=True),
                chat_id=query.message.chat.id,
                message_id=query.message.message_id
            )


@client_bot_router.message(state=Post.buttons)
async def post_buttons(message: types.Message, state: FSMContext, bot: Bot):
    inline_link_re = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')  # noqa
    buttons = inline_link_re.findall(message.text)
    if not buttons:
        await message.answer("Вы неправильно отправили. Отправьте еще раз.")
    else:
        data = await state.get_data()
        markup = types.InlineKeyboardMarkup(**json.loads(data.get("markup")))
        chat_id = data.get("chat_id")
        message_id = data.get("message_id")
        new_markup = inline_kb.add_buttons_to_post(markup, buttons)
        await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=new_markup)
        await bot.send_message(chat_id, "Кнопки добавлены", reply_to_message_id=message_id,
                               reply_markup=reply_kb.main_menu())
        await state.clear()


async def broadcast_to_users(bot_token: str, message: types.Message, admin: int):
    users, count = await shortcuts.get_users(bot__token=bot_token)
    succeed, failed = 0, 0
    async with Bot(bot_token).context() as b:
        call = get_call_method(message, inline_kb.remove_buttons_from_post(message.reply_markup))
        for idx, user in enumerate(users, 1):
            if user.uid == admin:
                continue
            try:
                await b(call(user.uid))
            except (TelegramForbiddenError, TelegramBadRequest, TelegramNotFound):
                failed += 1
            except TelegramRetryAfter as e:
                failed += 1
                await asyncio.sleep(e.retry_after)
            else:
                succeed += 1
            finally:
                await asyncio.sleep(settings.SLEEP_TIME)
        await b.send_message(chat_id=admin,
                             text=strings.BROADCAST_RESULT.format(succeed=succeed, failed=failed))
    return count, succeed, failed


@client_bot_router.callback_query(EditPercentCallbackData.filter())
async def choose_percent(query: types.CallbackQuery, callback_data: EditPercentCallbackData):
    bot = await shortcuts.get_bot()
    bot.percent = callback_data.percent
    await bot.save()
    await query.answer(f"процентная ставка изменился: {callback_data.percent}%")
    await query.message.edit_text("Панель администратора", reply_markup=inline_kb.admin_buttons())


@client_bot_router.message(state=ChangePhoto.photo, content_types=[types.ContentType.PHOTO,
                                                                   types.ContentType.ANIMATION])
async def change_photo(message: types.Message, state: FSMContext):
    bot = await shortcuts.get_bot()
    if message.animation:
        file_id = message.animation.file_id
        bot.photo_is_gif = True
    else:
        file_id = message.photo[-1].file_id
        bot.photo_is_gif = False
    bot.photo = file_id
    await bot.save()
    await message.answer("Изменено ✅")
    await state.clear()


@client_bot_router.message(state=ChangeChannelLink.link)
async def change_channel_link(message: types.Message, state: FSMContext):
    bot = await shortcuts.get_bot()
    bot.news_channel = message.text
    await bot.save()
    await message.answer("Изменено ✅")
    await state.clear()


@client_bot_router.message(state=ChangeAdmin.uid)
async def change_admin(message: types.Message, state: FSMContext, bot: Bot):
    try:
        uid = int(message.text)
        main_bot_user = await shortcuts.get_main_bot_user(uid)
        if main_bot_user:
            try:
                await bot.send_chat_action(uid, action="typing")
            except (TelegramBadRequest, TelegramForbiddenError, TelegramNotFound):
                await message.answer("Пользователь не найден. Попросите его отправить команду /start боту.")
            else:
                bot_ = await shortcuts.get_bot()
                bot_.owner = main_bot_user
                await bot_.save()
                await message.answer("✅ Админ успешно изменен")
                await bot.send_message(uid,
                                       "Этот бот передается вам. Отправьте команду /admin, "
                                       "чтобы увидеть панель администратора.")
        else:
            await message.answer("Пользователь не найден. Попросите его отправить команду /start главному боту.")
    except ValueError:
        await message.answer("Неверный ид пользователя")
    else:
        await state.clear()


@client_bot_router.message(state=ChangeSupport.username_or_uid)
async def change_support(message: types.Message, state: FSMContext):
    support = message.text
    if len(support) > 32:
        await message.answer("Неверное username или ид")
    else:
        if "@" in support:
            support = support.replace("@", "")
        bot_ = await shortcuts.get_bot()
        bot_.support = support
        await bot_.save()
        await message.answer("✅ Успешно изменен")
        await state.clear()


@client_bot_router.message(F.chat.id.in_(settings.ADMIN_LIST), commands="stat")
async def statistics(message: types.Message):
    text = (f"Пользователей всего: {await shortcuts.get_all_users_count()}\n"
            f"Новые пользователи: {await shortcuts.get_new_users_count()}\n"
            f"Заработано всего: {await shortcuts.earned()}\n"
            f"Прибыль(Сегодня): {await shortcuts.earned_today()}\n"
            f"Заказов за сегодня: {await shortcuts.ordered_today()}\n")
    await message.answer(text)


@client_bot_router.callback_query(MandatorySubscription.filter())
async def mandatory_subscription_actions(query: types.CallbackQuery, callback_data: MandatorySubscription,
                                         state: FSMContext, bot: Bot):
    bot_obj = await shortcuts.get_bot()
    chats = await shortcuts.get_subscription_chats(bot_obj)
    match callback_data.action:
        case "switch":
            if bot_obj.mandatory_subscription is True:
                bot_obj.mandatory_subscription = False
                await query.answer("Выключен")
                await bot_obj.save()
            else:
                if chats:
                    bot_obj.mandatory_subscription = True
                    await query.answer("Включен")
                    await bot_obj.save()
                else:
                    await query.answer("Невозможно включить. Никакого чата нет. Сначала добавьте чат.", show_alert=True)
                    return
        case "add":
            await state.set_state(AddSubscriptionChat.chat_id)
            try:
                await query.message.delete()
            except TelegramBadRequest:
                await query.message.edit_reply_markup()
            await query.message.answer("Отправите ИД канала или группы", reply_markup=reply_kb.cancel())
            return
        case "remove":
            text = "Выберите, чтобы удалить\n\n"
            for idx, chat in enumerate(chats, start=1):
                text += f"{idx}) {html.link(chat.title, chat.username or chat.invite_link)}\n"
            await query.message.edit_text(
                text,
                reply_markup=inline_kb.choose_subscription_chat(chats),
                disable_web_page_preview=True
            )
            return
        case "choose-to-remove":
            if callback_data.id:
                chat = await shortcuts.get_subscription_chat(bot_obj, callback_data.id)
                if chat:
                    with suppress(TelegramBadRequest, TelegramForbiddenError):
                        await bot.revoke_chat_invite_link(chat.uid, chat.invite_link)
                    await chat.delete()
                chats = await shortcuts.get_subscription_chats(bot_obj)
                if not chats:
                    bot_obj.mandatory_subscription = False
                    await bot_obj.save()
        case None:
            await query.answer()
            await query.message.edit_text("Панель администратора", reply_markup=inline_kb.admin_buttons())
            return
    text = strings.get_subscription_chats(bot_obj.mandatory_subscription, chats)
    await query.message.edit_text(text, reply_markup=inline_kb.mandatory_subscription_status(
        bot_obj.mandatory_subscription, len(chats)), disable_web_page_preview=True)


@client_bot_router.message(state=AddSubscriptionChat.chat_id)
async def add_subscription_chat(message: types.Message, state: FSMContext, bot: Bot):
    chat_id = message.text
    await bot.send_chat_action(message.chat.id, "typing")
    bot_ = await shortcuts.get_bot()
    try:
        chat_info = await bot.get_chat(chat_id)
        invite_link = await bot.create_chat_invite_link(
            chat_info.id, name="Invite link for the smm bot"
        )
        await shortcuts.add_subscription_chat(bot_, chat_info, invite_link)
        await message.answer("✅ Чат добавлен", reply_markup=types.ReplyKeyboardRemove())
        chats = await shortcuts.get_subscription_chats(bot_)
        text = strings.get_subscription_chats(bot_.mandatory_subscription, chats)
        await message.answer(text, reply_markup=inline_kb.mandatory_subscription_status(
            bot_.mandatory_subscription, len(chats)), disable_web_page_preview=True)
    except (TelegramBadRequest, TelegramNotFound, TelegramForbiddenError):
        await message.answer("Чат не найден. "
                             "Убедитесь, что бот является администратором в чате "
                             "и имеет достаточные привилегии")
    except IntegrityError:
        await message.answer("Этот чат уже добавлен")
    else:
        await state.clear()


@client_bot_router.message(state=ImportUsers.file, content_types=[types.ContentType.DOCUMENT, types.ContentType.TEXT])
async def import_users_file(message: types.Message, state: FSMContext, bot: Bot):
    match message.content_type:
        case types.ContentType.DOCUMENT:
            if message.document.file_size > 2_500_000:
                await message.answer("Файл слишком большой")
                return
            path = Path(f"bot_data/{bot.id}/import-users")
            path.mkdir(parents=True, exist_ok=True)
            file_path = settings.BASE_DIR / path / f"{message.document.file_name}_{int(message.date.timestamp())}"
            msg = await message.answer("Файл скачивается...")
            await bot.download(message.document.file_id, file_path)
            msg = await msg.edit_text("Файл проверяется...")
            async with aiofiles.open(file_path) as file:
                lines = await file.readlines()
                for idx, line in enumerate(lines, start=1):
                    if line.rstrip().isdigit():
                        continue
                    else:
                        await msg.edit_text(f"Идентификатор пользователя неверен в строке {idx}\n"
                                            f"Отправьте правильный файл")
                        return
            await msg.edit_text("Файл проверен ✅ Он будет добавлен в ближайшее время. "
                                "Вы будете проинформированы после завершения.")
            await state.clear()
