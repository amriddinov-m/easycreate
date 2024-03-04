from aiogram.dispatcher.filters.callback_data import CallbackData


class MainMenuCallbackData(CallbackData, prefix="main-menu"):
    action: str = None


class BalanceCallbackData(CallbackData, prefix="balance"):
    action: str = None


class CountryCallbackData(CallbackData, prefix="country"):
    action: str
    country_code: str = ""
    page: int = 1


class OperatorCallbackData(CallbackData, prefix="operator"):
    country_code: str
    operator: str


class ProductCallbackData(CallbackData, prefix="product"):
    action: str = 'retrieve'
    country_code: str = ""
    product: str = None
    operator: str = ""
    page: int = 1


class OrderCallbackData(CallbackData, prefix="order"):
    action: str
    order_id: int


class OrderHistoryCallbackData(CallbackData, prefix="order-history"):
    action: str = "paginate"
    page: int = 1


class BalanceHistoryCallbackData(CallbackData, prefix="balance-history"):
    action: str = "paginate"
    page: int = 1


class AdminPanelCallbackData(CallbackData, prefix="admin"):
    action: str = None


class BroadcastCallbackData(CallbackData, prefix="broadcast"):
    action: str
    confirm: bool = None


class EditPercentCallbackData(CallbackData, prefix="edit-percent"):
    percent: int


class MandatorySubscription(CallbackData, prefix="mandatory-s"):
    action: str = None
    id: int = None