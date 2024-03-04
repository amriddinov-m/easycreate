from datetime import datetime

from pydantic import BaseModel, Field


class BillAmount(BaseModel):
    currency: str
    value: float


class BillStatus(BaseModel):
    value: str
    changed_date_time: datetime = Field(alias="changedDateTime")


class Bill(BaseModel):
    site_id: str = Field(alias="siteId")
    bill_id: str = Field(alias="billId")
    amount: BillAmount
    status: BillStatus
    comment: str = None
    custom_fields: dict = Field(None, alias="customFields")
    creation_date_time: datetime = Field(alias="creationDateTime")
    expiration_date_time: datetime = Field(alias="expirationDateTime")
    pay_url: str = Field(None, alias="payUrl")


class Payment(BaseModel):
    bill: Bill
    version: str = None


class BroadcastResult(BaseModel):
    is_going: bool = True
    users: int = 0
    sent: int = 0
    failed: int = 0
    succeed: int = 0
    paused: bool = False


class YooMoneyNotification(BaseModel):
    amount: str
    withdraw_amount: str = None
    codepro: str
    currency: str
    datetime: str
    label: str = None
    notification_type: str
    operation_id: str
    sender: str = None
    sha1_hash: str
    unaccepted: str = None
    test_notification: str = None


class PayokNotification(BaseModel):
    payment_id: int
    shop: int
    amount: float
    profit: float
    desc: str
    currency: str
    currency_amount: float
    sign: str
    email: str = None
    date: datetime = None
    method: str = None
    custom: list
