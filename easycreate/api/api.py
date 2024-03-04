from fastapi import APIRouter
from clientbot.api.api import api_router as clientbot_api_router

api_router = APIRouter()
api_router.include_router(clientbot_api_router, prefix="/client-bot")
