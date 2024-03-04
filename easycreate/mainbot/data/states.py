from aiogram.dispatcher.fsm.state import StatesGroup, State


class NewBot(StatesGroup):
    token = State()


class Broadcast(StatesGroup):
    message = State()
    confirmation = State()


class Transfer(StatesGroup):
    amount = State()


class Payout(StatesGroup):
    amount = State()
    method = State()
    wallet = State()
    confirmation = State()


class ChangeUserBalance(StatesGroup):
    bot_username = State()
    uid = State()
    sum = State()
