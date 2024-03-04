from datetime import datetime

from pydantic import BaseModel, Field


class FowpayPayout(BaseModel):
    success: str = None
    payout_id: int
    payout_wallet: str
    payout_wallet_type: str
    payout_amount: float
    payout_amount_down: float
    payout_commission: float = Field(None, alias="payout_comission")
    payout_commission_type: str = Field(None, alias="payout_comission_type")
    payout_status: str
    payout_date_success: datetime = None
