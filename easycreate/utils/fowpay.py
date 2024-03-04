import logging

from py_lava_api.LavaAPI import LavaAPI
from config import settings


class FowpayException(Exception):
    pass


def generate_payment_url(amount: float, order_id: str):
    amount = float(amount)
    lava = LavaAPI(settings.LAVA_SHOP_ID, settings.LAVA_KEY_SECRET, settings.LAVA_KEY_STILL, payment_webhook=f"{settings.HOST}/client-bot/payments/lava")
    payment = lava.get_invoice(amount, order_id)
    return payment.data["url"]
