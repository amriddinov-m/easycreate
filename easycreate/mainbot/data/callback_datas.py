from aiogram.dispatcher.filters.callback_data import CallbackData


class ChoosePercent(CallbackData, prefix='choose-percent'):
    percent: int


class EditPercent(CallbackData, prefix='edit-percent'):
    percent: int


class Broadcast(CallbackData, prefix="broadcast-confirm"):
    to_all: bool = False
    confirm: bool


class ControlPanel(CallbackData, prefix="control-panel"):
    action: str
    
class AdminYesNo(CallbackData, prefix="admin_yes_no"):
    action: str
    payout_id: int


class Transfer(CallbackData, prefix="transfer"):
    pass


class PayoutCallbackData(CallbackData, prefix="payout-money"):
    confirm: bool = None


class ControlBot(CallbackData, prefix="control-bot"):
    action: str
    confirm: bool = None


class DeleteBotRequest(CallbackData, prefix="delete-bot"):
    action: str
    bot_admin: int


class FowpayMethod(CallbackData, prefix="fowpay-method"):
    method: str = None
