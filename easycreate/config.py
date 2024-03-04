from pathlib import Path
from typing import Any

import pytz
import os
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseSettings, validator, DirectoryPath

DEBUG = os.environ.get("DEBUG", True)


class Settings(BaseSettings):
    BASE_DIR: DirectoryPath = Path(__file__).resolve().parent
    API_V1_STR: str = "/api/v1"
    HOST: str = "https://48e4-188-113-206-87.ngrok-free.app"
    WEBHOOK_PATH: str = "/bot{token}"
    WEBHOOK_URL: str = None
    BOT_TOKEN: str
    CLIENT_BOT_TOKEN: str
    LAVA_SHOP_ID: str
    LAVA_KEY_SECRET: str
    LAVA_KEY_STILL: str
    SMS_ACTIVATE_URL: str
    SMS_ACTIVATE_TOKEN: str
    PAYS: int = -1001775118846
    ADMIN: int = 558777027
    ADMIN_LIST: list = [ADMIN, 1265627599, 302942780, 999032740, 1799580112]
    ADMIN_USERNAME: str = "SanjarDS"
    DEFAULT_PHOTO: str = "assets/img.png"
    HISTORY_LIMIT: int = 6
    SLEEP_TIME: float = .3
    CRYPTOMUS_MERCHANT: str
    CRYPTOMUS_APPKEY: str
    DB_URL: str

    AAIO_ID: str
    AAIO_KEY: str
    AAIO_SECRET_1: str
    AAIO_SECRET_2: str

    ALLOWED_CONTENT_TYPES: list[str] = ["text",
                                        "photo",
                                        "audio",
                                        "video",
                                        "video_note",
                                        "voice", ]
    USED_UPDATE_TYPES: list[str] = [
        "message",
        "callback_query",
        "chat_member"
    ]

    TIMEZONE: str = "Europe/Moscow"
    timezone: Any = None

    @validator("WEBHOOK_URL")
    def webhook_url(cls, _, values: dict):
        return values.get("HOST") + values.get("WEBHOOK_PATH")

    @validator('timezone')
    def get_timezone(cls, _, values: dict):
        return pytz.timezone(values.get("TIMEZONE"))

    class Config:
        env_file_encoding = 'utf-8'

env_file = "prod.env"

settings = Settings(_env_file=env_file)

TORTOISE_ORM = {
    "connections": {"default": settings.DB_URL},
    "apps": {
        "models": {
            "models": ["aerich.models", "db.models"],
            "default_connection": "default",
        },
    },
}

scheduler = AsyncIOScheduler(jobstores={'default': SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")},
                             executors={'default': AsyncIOExecutor()},
                             job_defaults={'misfire_grace_time': 15 * 60})
