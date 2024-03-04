from builtins import enumerate
from aiogram import html

from db.models import Order, BalanceHistory, SubscriptionChat

COUNTRIES = {
    "0": {
        "name": "Россия"
    },
    "1": {
        "name": "Украина"
    },
    "2": {
        "name": "Казахстан"
    },
    "3": {
        "name": "Китай"
    },
    "4": {
        "name": "Филиппины"
    },
    "5": {
        "name": "Мьянма"
    },
    "6": {
        "name": "Индонезия"
    },
    "7": {
        "name": "Малайзия"
    },
    "8": {
        "name": "Кения"
    },
    "9": {
        "name": "Танзания"
    },
    "10": {
        "name": "Вьетнам"
    },
    "11": {
        "name": "Кыргызстан"
    },
    "12": {
        "name": "США (виртуальные)"
    },
    "13": {
        "name": "Израиль"
    },
    "14": {
        "name": "Гонконг"
    },
    "15": {
        "name": "Польша"
    },
    "16": {
        "name": "Англия"
    },
    "17": {
        "name": "Мадагаскар"
    },
    "18": {
        "name": "Дем. Конго"
    },
    "19": {
        "name": "Нигерия"
    },
    "20": {
        "name": "Макао"
    },
    "21": {
        "name": "Египет"
    },
    "22": {
        "name": "Индия"
    },
    "23": {
        "name": "Ирландия"
    },
    "24": {
        "name": "Камбоджа"
    },
    "25": {
        "name": "Лаос"
    },
    "26": {
        "name": "Гаити"
    },
    "27": {
        "name": "Кот д'Ивуар"
    },
    "28": {
        "name": "Гамбия"
    },
    "29": {
        "name": "Сербия"
    },
    "30": {
        "name": "Йемен"
    },
    "31": {
        "name": "ЮАР"
    },
    "32": {
        "name": "Румыния"
    },
    "33": {
        "name": "Колумбия"
    },
    "34": {
        "name": "Эстония"
    },
    "35": {
        "name": "Азербайджан"
    },
    "36": {
        "name": "Канада"
    },
    "37": {
        "name": "Марокко"
    },
    "38": {
        "name": "Гана"
    },
    "39": {
        "name": "Аргентина"
    },
    "40": {
        "name": "Узбекистан"
    },
    "41": {
        "name": "Камерун"
    },
    "42": {
        "name": "Чад"
    },
    "43": {
        "name": "Германия"
    },
    "44": {
        "name": "Литва"
    },
    "45": {
        "name": "Хорватия"
    },
    "46": {
        "name": "Швеция"
    },
    "47": {
        "name": "Ирак"
    },
    "48": {
        "name": "Нидерланды"
    },
    "49": {
        "name": "Латвия"
    },
    "50": {
        "name": "Австрия"
    },
    "51": {
        "name": "Беларусь"
    },
    "52": {
        "name": "Таиланд"
    },
    "53": {
        "name": "Сауд. Аравия"
    },
    "54": {
        "name": "Мексика"
    },
    "55": {
        "name": "Тайвань"
    },
    "56": {
        "name": "Испания"
    },
    "57": {
        "name": "Иран"
    },
    "58": {
        "name": "Алжир"
    },
    "59": {
        "name": "Словения"
    },
    "60": {
        "name": "Бангладеш"
    },
    "61": {
        "name": "Сенегал"
    },
    "62": {
        "name": "Турция"
    },
    "63": {
        "name": "Чехия"
    },
    "64": {
        "name": "Шри-Ланка"
    },
    "65": {
        "name": "Перу"
    },
    "66": {
        "name": "Пакистан"
    },
    "67": {
        "name": "Новая Зеландия"
    },
    "68": {
        "name": "Гвинея"
    },
    "69": {
        "name": "Мали"
    },
    "70": {
        "name": "Венесуэла"
    },
    "71": {
        "name": "Эфиопия"
    },
    "72": {
        "name": "Монголия"
    },
    "73": {
        "name": "Бразилия"
    },
    "74": {
        "name": "Афганистан"
    },
    "75": {
        "name": "Уганда"
    },
    "76": {
        "name": "Ангола"
    },
    "77": {
        "name": "Кипр"
    },
    "78": {
        "name": "Франция"
    },
    "79": {
        "name": "Папуа-Новая Гвинея"
    },
    "80": {
        "name": "Мозамбик"
    },
    "81": {
        "name": "Непал"
    },
    "82": {
        "name": "Бельгия"
    },
    "83": {
        "name": "Болгария"
    },
    "84": {
        "name": "Венгрия"
    },
    "85": {
        "name": "Молдова"
    },
    "86": {
        "name": "Италия"
    },
    "87": {
        "name": "Парагвай"
    },
    "88": {
        "name": "Гондурас"
    },
    "89": {
        "name": "Тунис"
    },
    "90": {
        "name": "Никарагуа"
    },
    "91": {
        "name": "Тимор-Лесте"
    },
    "92": {
        "name": "Боливия"
    },
    "93": {
        "name": "Коста Рика"
    },
    "94": {
        "name": "Гватемала"
    },
    "95": {
        "name": "ОАЭ"
    },
    "96": {
        "name": "Зимбабве"
    },
    "97": {
        "name": "Пуэрто-Рико"
    },
    "98": {
        "name": "Судан"
    },
    "99": {
        "name": "Того"
    },
    "100": {
        "name": "Кувейт"
    },
    "101": {
        "name": "Сальвадор"
    },
    "102": {
        "name": "Ливия"
    },
    "103": {
        "name": "Ямайка"
    },
    "104": {
        "name": "Тринидад и Тобаго"
    },
    "105": {
        "name": "Эквадор"
    },
    "106": {
        "name": "Свазиленд"
    },
    "107": {
        "name": "Оман"
    },
    "108": {
        "name": "Босния и Герцеговина"
    },
    "109": {
        "name": "Доминиканская Республика"
    },
    "110": {
        "name": "Сирия"
    },
    "111": {
        "name": "Катар"
    },
    "112": {
        "name": "Панама"
    },
    "113": {
        "name": "Куба"
    },
    "114": {
        "name": "Мавритания"
    },
    "115": {
        "name": "Сьерра-Леоне"
    },
    "116": {
        "name": "Иордания"
    },
    "117": {
        "name": "Португалия"
    },
    "118": {
        "name": "Барбадос"
    },
    "119": {
        "name": "Бурунди"
    },
    "120": {
        "name": "Бенин"
    },
    "121": {
        "name": "Бруней"
    },
    "122": {
        "name": "Багамы"
    },
    "123": {
        "name": "Ботсвана"
    },
    "124": {
        "name": "Белиз"
    },
    "125": {
        "name": "ЦАР"
    },
    "126": {
        "name": "Доминика"
    },
    "127": {
        "name": "Гренада"
    },
    "128": {
        "name": "Грузия"
    },
    "129": {
        "name": "Греция"
    },
    "130": {
        "name": "Гвинея-Бисау"
    },
    "131": {
        "name": "Гайана"
    },
    "132": {
        "name": "Исландия"
    },
    "133": {
        "name": "Коморы"
    },
    "134": {
        "name": "Сент-Китс и Невис"
    },
    "135": {
        "name": "Либерия"
    },
    "136": {
        "name": "Лесото"
    },
    "137": {
        "name": "Малави"
    },
    "138": {
        "name": "Намибия"
    },
    "139": {
        "name": "Нигер"
    },
    "140": {
        "name": "Руанда"
    },
    "141": {
        "name": "Словакия"
    },
    "142": {
        "name": "Суринам"
    },
    "143": {
        "name": "Таджикистан"
    },
    "144": {
        "name": "Монако"
    },
    "145": {
        "name": "Бахрейн"
    },
    "146": {
        "name": "Реюньон"
    },
    "147": {
        "name": "Замбия"
    },
    "148": {
        "name": "Армения"
    },
    "149": {
        "name": "Сомали"
    },
    "150": {
        "name": "Конго"
    },
    "151": {
        "name": "Чили"
    },
    "152": {
        "name": "Буркина-Фасо"
    },
    "153": {
        "name": "Ливан"
    },
    "154": {
        "name": "Габон"
    },
    "155": {
        "name": "Албания"
    },
    "156": {
        "name": "Уругвай"
    },
    "157": {
        "name": "Маврикий"
    },
    "158": {
        "name": "Бутан"
    },
    "159": {
        "name": "Мальдивы"
    },
    "160": {
        "name": "Гваделупа"
    },
    "161": {
        "name": "Туркменистан"
    },
    "162": {
        "name": "Французская Гвиана"
    },
    "163": {
        "name": "Финляндия"
    },
    "164": {
        "name": "Сент-Люсия"
    },
    "165": {
        "name": "Люксембург"
    },
    "166": {
        "name": "Сент-Винсент и Гренадин"
    },
    "167": {
        "name": "Экваториальная Гвинея"
    },
    "168": {
        "name": "Джибути"
    },
    "169": {
        "name": "Антигуа и Барбуда"
    },
    "170": {
        "name": "Острова Кайман"
    },
    "171": {
        "name": "Черногория"
    },
    "172": {
        "name": "Дания"
    },
    "173": {
        "name": "Швейцария"
    },
    "174": {
        "name": "Норвегия"
    },
    "175": {
        "name": "Австралия"
    },
    "176": {
        "name": "Эритрея"
    },
    "177": {
        "name": "Южный Судан"
    },
    "178": {
        "name": "Сан-Томе и Принсипи"
    },
    "179": {
        "name": "Аруба"
    },
    "180": {
        "name": "Монтсеррат"
    },
    "181": {
        "name": "Ангилья"
    },
    "182": {
        "name": "Япония"
    },
    "183": {
        "name": "Северная Македония"
    },
    "184": {
        "name": "Республика Сейшелы"
    },
    "185": {
        "name": "Новая Каледония"
    },
    "186": {
        "name": "Кабо-Верде"
    },
    "187": {
        "name": "США"
    },
    "188": {
        "name": "Палестина"
    },
    "189": {
        "name": "Фиджи"
    },
    "190": {
        "name": "Южная Корея"
    },
    "191": {
        "name": "Северная Корея"
    },
    "192": {
        "name": "Западная Сахара"
    },
    "193": {
        "name": "Соломоновы острова"
    },
    "194": {
        "name": "Джерси"
    },
    "195": {
        "name": "Бермуды"
    },
    "196": {
        "name": "Сингапур"
    },
    "197": {
        "name": "Тонга"
    },
    "198": {
        "name": "Самоа"
    },
    "199": {
        "name": "Мальта"
    },
    "200": {
        "name": "Лихтенштейн"
    }
}

SERVICES = {
    "full": {
        "name": "Полная аренда"
    },
    "vk": {
        "name": "Вконтакте"
    },
    "ok": {
        "name": "Одноклассники"
    },
    "wa": {
        "name": "Whatsapp"
    },
    "vi": {
        "name": "Viber"
    },
    "tg": {
        "name": "Telegram"
    },
    "wb": {
        "name": "WeCha"
    },
    "go": {
        "name": "Google"
    },
    "av": {
        "name": "avito"
    },
    "fb": {
        "name": "facebook"
    },
    "tw": {
        "name": "Twitter"
    },
    "ub": {
        "name": "Uber"
    },
    "ig": {
        "name": "Instagram"
    },
    "ym": {
        "name": "Юла"
    },
    "ma": {
        "name": "Mail.ru"
    },
    "mm": {
        "name": "Microsoft"
    },
    "uk": {
        "name": "Airbnb"
    },
    "me": {
        "name": "Line messenger"
    },
    "mb": {
        "name": "Yahoo"
    },
    "bd": {
        "name": "пятёрочка"
    },
    "dt": {
        "name": "Delivery Club"
    },
    "ya": {
        "name": "Яндекс"
    },
    "mt": {
        "name": "Steam"
    },
    "oi": {
        "name": "Tinder"
    },
    "fd": {
        "name": "Mamba"
    },
    "kt": {
        "name": "KakaoTalk"
    },
    "pm": {
        "name": "AOL"
    },
    "tn": {
        "name": "LinkedIN"
    },
    "qq": {
        "name": "Tencent QQ"
    },
    "mg": {
        "name": "Магнит"
    },
    "yl": {
        "name": "Yalla"
    },
    "po": {
        "name": "premium.one"
    },
    "nv": {
        "name": "Naver"
    },
    "nf": {
        "name": "Netflix"
    },
    "ds": {
        "name": "Discord"
    },
    "lf": {
        "name": "TikTok"
    },
    "zh": {
        "name": "Zoho"
    },
    "gp": {
        "name": "Ticketmaster"
    },
    "am": {
        "name": "Amazon"
    },
    "dp": {
        "name": "ProtonMail"
    },
    "yf": {
        "name": "Citymobil"
    },
    "fx": {
        "name": "PGbonus"
    },
    "qr": {
        "name": "MEGA"
    },
    "yk": {
        "name": "СпортМастер"
    },
    "ls": {
        "name": "Careem"
    },
    "bl": {
        "name": "BIGO LIVE"
    },
    "fu": {
        "name": "Snapchat"
    },
    "sg": {
        "name": "OZON"
    },
    "uu": {
        "name": "Wildberries"
    },
    "ua": {
        "name": "BlaBlaCar"
    },
    "ce": {
        "name": "mosru"
    },
    "tx": {
        "name": "Bolt"
    },
    "ip": {
        "name": "Burger King"
    },
    "hw": {
        "name": "Alipay"
    },
    "de": {
        "name": "карусель"
    },
    "jc": {
        "name": "IVI"
    },
    "rl": {
        "name": "inDriver"
    },
    "df": {
        "name": "Happn"
    },
    "kf": {
        "name": "Weib"
    },
    "za": {
        "name": "JDcom"
    },
    "da": {
        "name": "MTS CashBack"
    },
    "ot": {
        "name": "Любой другой"
    },
    "li": {
        "name": "Baidu"
    },
    "dz": {
        "name": "Dominos Pizza"
    },
    "rd": {
        "name": "Lenta"
    },
    "ew": {
        "name": "Nike"
    },
    "ae": {
        "name": "myGLO"
    },
    "gb": {
        "name": "YouStar"
    },
    "cy": {
        "name": "РСА"
    },
    "yw": {
        "name": "Grindr"
    },
    "ts": {
        "name": "PayPal"
    },
    "bz": {
        "name": "Blizzard"
    },
    "xk": {
        "name": "Di"
    },
    "sd": {
        "name": "dodopizza"
    },
    "wc": {
        "name": "Craigslist"
    },
    "mj": {
        "name": "Zalo"
    },
    "pp": {
        "name": "Huya"
    },
    "xr": {
        "name": "Tango"
    },
    "tk": {
        "name": "МВидеоМ"
    },
    "yo": {
        "name": "Amasia"
    },
    "st": {
        "name": "Ашан"
    },
    "il": {
        "name": "IQOS"
    },
    "an": {
        "name": "Adidas"
    },
    "jr": {
        "name": "Самокат"
    },
    "wx": {
        "name": "Apple"
    },
    "lb": {
        "name": "Mailru Group"
    },
    "lt": {
        "name": "BitClout"
    },
    "jf": {
        "name": "Likee"
    },
    "rj": {
        "name": "Детский мир"
    },
    "es": {
        "name": "iQIYI"
    },
    "be": {
        "name": "Сбер Мега Маркет"
    },
    "gm": {
        "name": "Mocospace"
    },
    "hg": {
        "name": "Switips"
    },
    "qz": {
        "name": "Faceit"
    },
    "gz": {
        "name": "LYKA"
    },
    "sh": {
        "name": "Вкус Вилл"
    },
    "qf": {
        "name": "RedBook"
    },
    "nq": {
        "name": "Trip"
    },
    "ke": {
        "name": "Эльдорадо"
    },
    "ol": {
        "name": "KazanExpress"
    },
    "xj": {
        "name": "Сбер Маркет"
    },
    "kz": {
        "name": "NimoTV"
    },
    "hb": {
        "name": "Twitch"
    },
    "xe": {
        "name": "GalaxyChat"
    },
    "io": {
        "name": "ЗдравСити"
    },
    "sl": {
        "name": "СберАптека"
    },
    "wp": {
        "name": "163СOM"
    },
    "en": {
        "name": "Hermes"
    },
    "zo": {
        "name": "Kaggle"
    },
    "bo": {
        "name": "Wise"
    },
    "fz": {
        "name": "KFC"
    },
    "vm": {
        "name": "OkCupid"
    },
    "og": {
        "name": "Okko"
    },
    "yz": {
        "name": "Около"
    },
    "ft": {
        "name": "Букмекерские"
    },
    "lv": {
        "name": "Megogo"
    },
    "lx": {
        "name": "DewuPoison"
    },
    "ee": {
        "name": "Twilio"
    },
    "yu": {
        "name": "Xiaomi"
    },
    "sb": {
        "name": "Lamoda"
    },
    "aw": {
        "name": "Taikang"
    },
    "ta": {
        "name": "Wink"
    },
    "vj": {
        "name": "Stormgain"
    },
    "sz": {
        "name": "Pivko24"
    },
    "cr": {
        "name": "TenChat"
    },
    "of": {
        "name": "Urent"
    },
    "gk": {
        "name": "AptekaRU"
    },
    "cu": {
        "name": "炙热星河"
    },
    "mi": {
        "name": "Zupee"
    },
    "rc": {
        "name": "Skype"
    },
    "ba": {
        "name": "Expressmoney"
    },
    "ai": {
        "name": "CELEBe"
    },
    "nw": {
        "name": "Ximalaya"
    },
    "xx": {
        "name": "Joyride"
    },
    "br": {
        "name": "Вкусно и Точка"
    },
    "kj": {
        "name": "YAPPY"
    },
    "xm": {
        "name": "Лэтуаль"
    },
    "bi": {
        "name": "勇仕网络Ys4fun"
    },
    "yd": {
        "name": "米画师Mihuashi"
    },
    "zx": {
        "name": "CommunityGaming"
    },
    "dj": {
        "name": "LUKOIL-AZS"
    },
    "ao": {
        "name": "UU163"
    }
}

WELCOME = ("Привет, {name}!\n"
           "При помощи этого бота ты можешь принимать сообщения на номера, "
           "которые я дам, тем самым регистрироваться на разных сайтах и соц.сетях")
MAIN_MENU = "Главное меню"
BALANCE = ("💲 Ваш баланс: {balance}₽\n"
           "🏷 Ваш id: <code>{uid}</code>")
BALANCE_CHARGED = "🎊 Ваш баланс успешно пополнен на {} ₽"
BACK = "Назад"
CANCEL = "Отмена"
BROADCAST = ("🗣 Отправьте одно сообщение которое хотите разослать всем пользователям. "
             "Отправка сообщения занимает около {} секунды")
BROADCAST_RESULT = (
    "Послал: {succeed}\n"
    "Не удалось отправить: {failed}"
)
INFO = ("{username} - уникальный сервис для приёма SMS сообщений\n\n"
        "Наши преимущества:\n"
        "✔️ Низкие цены\n"
        "✔️ Полная автоматизация\n"
        "✔️ Быстрота и удобство\n"
        "✔️ Разнообразие сервисов и стран\n"
        "✔️ Партнёрская программа\n"
        "✔️ Постоянные обновления\n"
        "✔️ Отзывчивая поддержка")

PARTNERSHIP = ("👥 Партнёрская программа 👥\n"
               "➖➖➖➖➖➖➖➖➖➖\n"
               "▫️ В нашем боте действует одноуровневая партнёрская программа с "
               "оплатой за каждый купленный рефералом номер. "
               "В будущем планируем добавить до 3 уровней партнерской программы\n"
               "▫️ 1 уровень - 0.25₽ за номер: 1 партнёров принесли 0.25₽\n"
               "🔗 Ваша партнёрская ссылка:\n"
               "{link}")

NOTHING_FOUND = "Ничего не найдено!"

def get_num(text: str) -> str:
    a = text.split(":")
    b = a[1] if len(a) > 0 else a
    return b

async def print_order_history(orders: list["Order"]):
    text = []
    for order in orders:
        text.append(
            f"🧾 Заказ №: {order.order_id}\n"
            f"💴 Цена: {order.calculated_price:.2f}₽\n"
            f"📱 Сервис: <code>{order.product}</code>\n"
            f"📱 Номер: <code>{order.phone}</code>\n"
            f"📊 Код: {order.receive_code}\n"
        )
    return "\n".join(text) if text else None


def print_balance_history(items: list["BalanceHistory"]):
    text = []
    for item in items:
        text.append(
            f"💲 Сумма: {item.amount:+.2f}₽\n"
            f"💰 Баланс: {item.balance}₽\n"
            f"ℹ️ Источник: {item.source}\n"
            f"📅 Дата: {item.created_at.strftime('%d-%m-%Y %H:%M')}\n"
        )
    return "\n".join(text) if text else None

def get_subscription_chats(is_turned_on: bool, chats: list["SubscriptionChat"] = None):
    text = "Статус: ✅ включен\n" if is_turned_on else "Статус: ☑️ выключен\n"
    text += "\nЧаты:\n"
    for idx, chat in enumerate(chats, 1):
        text += f"{idx}) {html.link(chat.title, chat.invite_link)}\n"
    return text


LAVA_METHOD = [
    {
        "name": "Лава",
        "code": "lava",
        "min": 10,
        "max": 50000
    },
    {
        "name": "QIWI",
        "code": "qiwi",
        "min": 10,
        "max": 50000
    },
    {
        "name": "Карта",
        "code": "card",
        "min": 15,
        "max": 50000
    },
]

LAVA_METHOD_MAIN = [
    {
        "name": "Лава",
        "code": "lava",
        "min": 10,
        "max": 50000
    },
    {
        "name": "QIWI",
        "code": "qiwi",
        "min": 15,
        "max": 50000
    },
    {
        "name": "Карта",
        "code": "card",
        "min": 1000,
        "max": 50000
    },
]