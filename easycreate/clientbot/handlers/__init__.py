from .cancel import client_bot_router
from .admin_panel import client_bot_router
from .balance import client_bot_router
from .error_handler import client_bot_router
from .main import client_bot_router
from .order_history import client_bot_router
from .ordering import client_bot_router
from .subscription import client_bot_router

__all__ = ['client_bot_router']
