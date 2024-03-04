from dataclasses import dataclass
from pydantic import BaseModel

class LavaBillItem(BaseModel):
    invoice_id: str
    status: str
    pay_time: str
    amount: str
    order_id: str
    pay_service: str
    payer_details: str
    credited: str    

class LavaPayoutItem(BaseModel):
    payoff_id: str
    status: str
    payoff_time: str
    payoff_service: str
    type: str
    credited: str
    order_id: str
    
@dataclass
class OrderNumberResponse:
    order_id: int
    phone: str