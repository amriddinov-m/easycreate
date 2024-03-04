from aiogram.dispatcher.fsm.state import StatesGroup, State


class RefillAmount(StatesGroup):
    amount = State()
    method = State()

class RefillAmount(StatesGroup):
    amount = State()
    method = State()
    crypto = State()

class CountryState(StatesGroup):
    search = State()


class ProductState(StatesGroup):
    search = State()


class BroadcastState(StatesGroup):
    message = State()
    confirmation = State()


class ChangePhoto(StatesGroup):
    photo = State()


class ChangeChannelLink(StatesGroup):
    link = State()


class ChangeAdmin(StatesGroup):
    uid = State()


class ChangeSupport(StatesGroup):
    username_or_uid = State()


class Post(StatesGroup):
    buttons = State()


class AddSubscriptionChat(StatesGroup):
    chat_id = State()


class ImportUsers(StatesGroup):
    file = State()
