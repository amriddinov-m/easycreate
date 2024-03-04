import enum
from datetime import datetime, timezone

from tortoise import fields, Model

class BaseModel(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-id']

class User(BaseModel):
    uid = fields.BigIntField(unique=True)
    username = fields.CharField(max_length=255, null=True)
    first_name = fields.CharField(max_length=255)
    last_name = fields.CharField(max_length=255, null=True)
    is_admin = fields.BooleanField(default=False)


class MainBotUser(BaseModel):
    user: fields.OneToOneRelation[User] = fields.OneToOneField('models.User', on_delete=fields.CASCADE,
                                                               related_name="main_bot_user")
    uid = fields.BigIntField(unique=True)
    balance = fields.FloatField(default=0)
    referral_count = fields.IntField(default=0)
    referral_balance = fields.FloatField(default=0)

    bots: fields.ReverseRelation["Bot"]


class Bot(BaseModel):
    token = fields.CharField(max_length=255, unique=True)
    owner: fields.ForeignKeyRelation[MainBotUser] = fields.ForeignKeyField('models.MainBotUser',
                                                                           on_delete=fields.CASCADE,
                                                                           related_name="bots")
    percent = fields.IntField()
    username = fields.CharField(max_length=255)
    unauthorized = fields.BooleanField(default=False)
    photo = fields.CharField(max_length=255, null=True)
    photo_is_gif = fields.BooleanField(default=False)
    clients: fields.ReverseRelation["ClientBotUser"]
    news_channel = fields.CharField(max_length=255, null=True)
    support = fields.CharField(max_length=32, null=True)
    mandatory_subscription = fields.BooleanField(default=False)
    subscription_chats_changed_at = fields.DatetimeField(default=datetime(1970, 1, 1, tzinfo=timezone.utc))


class ClientBotUser(BaseModel):
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField('models.User', on_delete=fields.CASCADE,
                                                                   related_name="client_bot_users")
    bot: fields.ForeignKeyRelation[Bot] = fields.ForeignKeyField('models.Bot', on_delete=fields.CASCADE,
                                                                 related_name="clients")
    uid = fields.BigIntField()
    balance = fields.FloatField(default=0)
    referral_count = fields.IntField(default=0)
    inviter = fields.ForeignKeyField("models.ClientBotUser", on_delete=fields.SET_NULL, null=True)
    subscribed_all_chats = fields.BooleanField(default=False)
    subscribed_chats_at = fields.DatetimeField(default=datetime(1970, 1, 1, tzinfo=timezone.utc))


class RefillSource(enum.Enum):
    QIWI = "QIWI"
    ADMIN = "Administrator"
    YOOMONEY = "YooMoney"
    REFERRAL = "Реферал"


class BalanceHistory(BaseModel):
    """
        {
                "ID": 119307479,
                "TypeName": "buy",
                "Source": "telegram",
                "Amount": -45,
                "Balance": 10,
                "CreatedAt": "2022-03-04T06:32:43.983682Z"
            },
            {
                "ID": 119307226,
                "TypeName": "charge",
                "Source": "qiwi",
                "Amount": 50,
                "Balance": 55,
                "CreatedAt": "2022-03-04T06:31:02.71514Z"
            },
        """

    class TypeName(str, enum.Enum):
        BUY = "buy"
        CHARGE = "charge"

    amount = fields.FloatField()
    balance = fields.FloatField()
    source = fields.CharField(max_length=255)
    type_name = fields.CharEnumField(TypeName)
    client_bot_user = fields.ForeignKeyField("models.ClientBotUser", null=True)
    main_bot_user = fields.ForeignKeyField("models.MainBotUser", null=True)

class BanModel(BaseModel):
    user = fields.ForeignKeyField("models.ClientBotUser", on_delete=fields.CASCADE)
    service = fields.CharField(max_length=100)
    phone = fields.CharField(max_length=50)

class Order(BaseModel):
    user = fields.ForeignKeyField("models.ClientBotUser", on_delete=fields.CASCADE)
    order_id = fields.BigIntField(unique=True)
    country = fields.CharField(max_length=100)
    country_code = fields.CharField(max_length=20, default="")
    operator = fields.CharField(max_length=255)
    product = fields.CharField(max_length=255)
    phone = fields.CharField(max_length=255)
    receive_code = fields.CharField(max_length=255, default="")
    receive_status = fields.CharField(max_length=10, default="")
    price = fields.FloatField()
    order_created_at = fields.DatetimeField()
    calculated_price = fields.FloatField(default=0)
    profit = fields.FloatField(default=0)
    bot_admin_profit = fields.FloatField(default=0)


class BillStatus(enum.Enum):
    PAID = "PAID"
    WAITING = "WAITING"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class BillHistory(BaseModel):
    user = fields.ForeignKeyField("models.ClientBotUser")
    bill_id = fields.CharField(max_length=255, unique=True)
    comment = fields.TextField(null=True)
    amount = fields.FloatField()
    status = fields.CharEnumField(BillStatus, null=True)


class SubscriptionChat(BaseModel):
    bot = fields.ForeignKeyField("models.Bot")
    title = fields.CharField(max_length=65)
    uid = fields.BigIntField()
    username = fields.CharField(max_length=32, null=True)
    invite_link = fields.CharField(max_length=255, null=True)
    type = fields.CharField(max_length=100)

    class Meta:
        unique_together = ('bot', 'uid')


class Payout(BaseModel):
    """
    {
        "success" : "Payout created",
        "payout_id" : "32",
        "payout_wallet" : "74999905568",
        "payout_wallet_type" : "qiwi",
        "payout_amount" : "100.00",
        "payout_amount_down" : "103.00",
        "payout_comission" : "3.00",
        "payout_comission_type" : "balance" | "payment",
        "payout_status" : "wait" | "success" | "cancel"
    }
    """
    user = fields.ForeignKeyField("models.MainBotUser")
    success = fields.CharField(max_length=255)
    payout_id = fields.CharField(max_length=255)
    payout_wallet = fields.CharField(max_length=255)
    payout_wallet_type = fields.CharField(max_length=255)
    payout_amount = fields.FloatField()
    payout_amount_down = fields.FloatField()
    payout_commission = fields.FloatField()
    payout_commission_type = fields.CharField(max_length=255)
    payout_status = fields.CharField(max_length=255)
    payout_date_success = fields.DatetimeField(null=True)
