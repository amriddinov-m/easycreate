from fastapi import APIRouter

from .endpoints import payments
from .endpoints import payouts

api_router = APIRouter()
api_router.include_router(payments.router, prefix="/payments")
api_router.include_router(payouts.router, prefix="/payouts")
