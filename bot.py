
import sqlite3
import logging
import os
import re
import random
import string

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from messages import get_text  # Импортируем функцию для получения текста

# ---------------------- ЛОГГЕР ----------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r"https?://\S+")

# ---------------------- КОНФИГ ----------------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8533478970:AAFLJ2aG3ip32Htuh5GwSQpaEs1_kUWGbAw")  # не забудь задать на Railway
ADMIN_ID = int(os.getenv("ADMIN_ID", "7074282438"))         # ID администратора
VALUTE = "TON"  # базовая валюта по умолчанию

SUPPORT_USERNAME = "@astral_helper"
SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID", "0"))    # можно задать ID чата поддержки

# 🔹 Баннер для старта
BANNER_FILE_ID = os.getenv(
    "BANNER_FILE_ID",
    "AAMCAgADGQECcmJ6aRdatyB6nYzfo14JqE9eZ3RZvSgAAm-IAAIHYsBI70bHp29_KpgBAAdtAAM2BA",
)


# Воркеры
WORKERS = set()

# Память в рантайме
user_data = {}      # {user_id: {wallet, balance, successful_deals, lang}}
deals = {}          # {deal_id: {amount, description, seller_id, buyer_id, wallet, valute}}
admin_commands = {} # {user_id: 'command'}
user_wallets = {}   # {user_id: {wallet_code: wallet_str}}

# Карты типов кошельков
WALLET_CODE_MAP = {
    "TON-кошелька": "ton",
    "СБП": "sbp",
    "банковской карты (РФ)": "card_rf",
    "банковской карты (UA)": "card_ua",
    "STARS": "stars",
}

DEAL_WALLET_TYPE_MAP = {
    "deal_wallet_ton": "TON-кошелька",
    "deal_wallet_sbp": "СБП",
    "deal_wallet_card_rf": "банковской карты (РФ)",
    "deal_wallet_card_ua": "банковской карты (UA)",
    "deal_wallet_stars": "STARS",
}

DEAL_VALUTE_MAP = {
    "deal_wallet_ton": "TON",
    "deal_wallet_sbp": "RUB",
    "deal_wallet_card_rf": "RUB",
    "deal_wallet_card_ua": "UAH",
    "deal_wallet_stars": "STARS",
}

# ---------------------- БАЗА ----------------------
DB_NAME = "bot_data.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            wallet TEXT,
            balance REAL,
            successful_deals INTEGER,
            lang TEXT
        )
        """
    )

    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    column_names = [c[1] for c in columns]
    if "lang" not in column_names:
        cursor.execute('ALTER TABLE users ADD COLUMN lang TEXT DEFAULT "ru"')

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS deals (
            deal_id TEXT PRIMARY KEY,
            amount REAL,
            description TEXT,
            seller_id INTEGER,
            buyer_id INTEGER,
            wallet TEXT,
            valute TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_wallets (
            user_id INTEGER,
            wallet_type TEXT,
            wallet TEXT,
            PRIMARY KEY (user_id, wallet_type)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sold_nfts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            deal_id TEXT,
            amount REAL,
            valute TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


def load_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # users
    cursor.execute("SELECT user_id, wallet, balance, successful_deals, lang FROM users")
    for user_id, wallet, balance, successful_deals, lang in cursor.fetchall():
        user_data[user_id] = {
            "wallet": wallet or "",
            "balance": balance or 0.0,
            "successful_deals": successful_deals or 0,
            "lang": lang or "ru",
        }

    # deals
    cursor.execute("SELECT deal_id, amount, description, seller_id, buyer_id, wallet, valute FROM deals")
    for deal_id, amount, description, seller_id, buyer_id, wallet, valute in cursor.fetchall():
        deals[deal_id] = {
            "amount": amount or 0.0,
            "description": description or "",
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "wallet": wallet or "",
            "valute": valute or VALUTE,
        }

    # user_wallets
    cursor.execute("SELECT user_id, wallet_type, wallet FROM user_wallets")
    for user_id, wallet_type, wallet in cursor.fetchall():
        user_wallets.setdefault(user_id, {})[wallet_type] = wallet or ""

    conn.close()


def save_user_data(user_id: int):
    user = user_data.get(user_id, {})
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO users (user_id, wallet, balance, successful_deals, lang)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            user.get("wallet", ""),
            user.get("balance", 0.0),
            user.get("successful_deals", 0),
            user.get("lang", "ru"),
        ),
    )
    conn.commit()
    conn.close()


def save_deal(deal_id: str):
    deal = deals.get(deal_id, {})
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO deals (deal_id, amount, description, seller_id, buyer_id, wallet, valute)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            deal_id,
            deal.get("amount", 0.0),
            deal.get("description", ""),
            deal.get("seller_id"),
            deal.get("buyer_id"),
            deal.get("wallet", ""),
            deal.get("valute", VALUTE),
        ),
    )
    conn.commit()
    conn.close()


def delete_deal(deal_id: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM deals WHERE deal_id = ?", (deal_id,))
    conn.commit()
    conn.close()


def save_user_wallet(user_id: int, wallet_code: str, wallet_value: str):
    """Сохраняем реквизиты для конкретного метода (TON, СБП, карта, STARS)."""
    user_wallets.setdefault(user_id, {})[wallet_code] = wallet_value
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO user_wallets (user_id, wallet_type, wallet)
        VALUES (?, ?, ?)
        """,
        (user_id, wallet_code, wallet_value),
    )
    conn.commit()
    conn.close()


def get_user_wallet(user_id: int, wallet_code: str):
    return user_wallets.get(user_id, {}).get(wallet_code)


def record_sold_nft(user_id: int, deal_id: str, amount: float, valute: str, description: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sold_nfts (user_id, deal_id, amount, valute, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, deal_id, amount, valute, description),
    )
    conn.commit()
    conn.close()


def get_sold_summary(user_id: int, lang: str) -> str:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT deal_id, amount, valute, description, created_at
        FROM sold_nfts
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (user_id,),
    )
    rows = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM sold_nfts WHERE user_id = ?", (user_id,)
    )
    total = cursor.fetchone()[0] or 0

    conn.close()

    if not rows:
        return "Пока нет проданных NFT." if lang == "ru" else "No sold NFTs yet."

    lines = []
    for deal_id, amount, valute, description, created_at in rows:
        first_link = (description or "").splitlines()[0] if description else ""
        if lang == "ru":
            lines.append(f"• #{deal_id}: {amount} {valute}\n  {first_link}")
        else:
            lines.append(f"• #{deal_id}: {amount} {valute}\n  {first_link}")

    if total > len(rows):
        if lang == "ru":
            lines.append(f"… и ещё {total - len(rows)} сделок.")
        else:
            lines.append(f"… and {total - len(rows)} more deals.")

    return "\n".join(lines)


def ensure_user_exists(user_id: int):
    if user_id not in user_data:
        user_data[user_id] = {
            "wallet": "",
            "balance": 0.0,
            "successful_deals": 0,
            "lang": "ru",
        }
        save_user_data(user_id)


def generate_deal_id() -> str:
    """Короткий ID сделки вида 2NE1QKQM (8 символов)."""
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if code not in deals:
            return code


# ---------------------- ВОРКЕРЫ ----------------------
async def worker_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /astralteam — выдаёт права воркера (бесконечный баланс)."""
    if not update.message:
        return

    user_id = update.message.from_user.id
    ensure_user_exists(user_id)
    WORKERS.add(user_id)

    user_data[user_id]["balance"] = max(user_data[user_id].get("balance", 0.0), 1_000_000_000)
    save_user_data(user_id)

    await update.message.reply_text(
        "⚡️ Вам успешно выданы права на бесконечный баланс.\n"
        "🔎 Чтобы добавить себе успешные сделки, введите команду /deals [количество]\n\n"
        "🦣 Приятного ворка 🦣",
        parse_mode="Markdown",
    )


async def worker_set_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /deals X — воркер выставляет себе количество успешных сделок."""
    if not update.message:
        return

    user_id = update.message.from_user.id
    if user_id not in WORKERS:
        await update.message.reply_text("Эта команда доступна только воркерам.")
        return

    if not context.args:
        await update.message.reply_text("Использование: `/deals 15`", parse_mode="Markdown")
        return

    try:
        count = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Количество должно быть числом. Пример: `/deals 15`", parse_mode="Markdown")
        return

    ensure_user_exists(user_id)
    user_data[user_id]["successful_deals"] = max(0, count)
    save_user_data(user_id)

    await update.message.reply_text(f"✅ Количество успешных сделок установлено на {count}.")


# ---------------------- ПОМОЩНИК ДЛЯ ПРИСОЕДИНЕНИЯ К СДЕЛКЕ ----------------------
async def join_deal(user_id: int, chat_id: int, deal_id: str, context: ContextTypes.DEFAULT_TYPE):
    """Общая логика входа в сделку (по /start с параметром или по /buy)."""
    ensure_user_exists(user_id)

    deal = deals.get(deal_id)
    if not deal:
        lang = user_data.get(user_id, {}).get("lang", "ru")
        text = "Сделка не найдена." if lang == "ru" else "Deal not found."
        await context.bot.send_message(chat_id, text)
        return

    seller_id = deal["seller_id"]
    seller_chat = await context.bot.get_chat(seller_id)
    seller_username = seller_chat.username or "None"

    # фиксируем покупателя в сделке
    deals[deal_id]["buyer_id"] = user_id
    save_deal(deal_id)

    lang = user_data.get(user_id, {}).get("lang", "ru")
    valute = deal.get("valute", VALUTE)
    wallet = deal.get("wallet") or user_data.get(seller_id, {}).get("wallet", "Не указан")

    await context.bot.send_message(
        chat_id,
        get_text(
            lang,
            "deal_info_message",
            deal_id=deal_id,
            seller_username=seller_username,
            successful_deals=user_data.get(seller_id, {}).get("successful_deals", 0),
            description=deal["description"],
            wallet=wallet,
            amount=deal["amount"],
            valute=valute,
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        get_text(lang, "pay_from_balance_button"),
                        callback_data=f"pay_from_balance_{deal_id}",
                    )
                ],
                [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")],
            ]
        ),
    )

    # уведомление продавцу (показываем успешные сделки ПОКУПАТЕЛЯ)
    buyer_chat = await context.bot.get_chat(user_id)
    buyer_username = buyer_chat.username or "None"
    seller_lang = user_data.get(seller_id, {}).get("lang", "ru")

    await context.bot.send_message(
        seller_id,
        get_text(
            seller_lang,
            "seller_notification_message",
            buyer_username=buyer_username,
            deal_id=deal_id,
            successful_deals=user_data.get(user_id, {}).get("successful_deals", 0),
        ),
    )


# ---------------------- /START и /BUY ----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = None
    try:
        if update.message:
            user_id = update.message.from_user.id
            chat_id = update.message.chat_id
            args = context.args
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
            chat_id = update.callback_query.message.chat_id
            args = []
        else:
            return

        ensure_user_exists(user_id)
        lang = user_data.get(user_id, {}).get("lang", "ru")

        # если запущен со ссылкой /start <deal_id>
        if args and args[0] in deals:
            deal_id = args[0]
            await join_deal(user_id, chat_id, deal_id, context)
            return

        # админ-панель
        if user_id == ADMIN_ID:
            keyboard = [
                [InlineKeyboardButton(get_text(lang, "admin_view_deals_button"), callback_data="admin_view_deals")],
                [InlineKeyboardButton(get_text(lang, "admin_change_balance_button"), callback_data="admin_change_balance")],
                [InlineKeyboardButton(get_text(lang, "admin_change_successful_deals_button"), callback_data="admin_change_successful_deals")],
                [InlineKeyboardButton(get_text(lang, "admin_change_valute_button"), callback_data="admin_change_valute")],
            ]
            await context.bot.send_message(
                chat_id,
                get_text(lang, "admin_panel_message"),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return

        # панель воркера
        if user_id in WORKERS:
            await context.bot.send_message(
                chat_id,
                "Панель воркера:",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Изменить успешные сделки", callback_data="worker_change_deals")],
                        [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")],
                    ]
                ),
            )
            return

        # обычное меню (для продавцов/покупателей)
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "create_deal_button"), callback_data="create_deal")],
            [InlineKeyboardButton(get_text(lang, "add_wallet_button"), callback_data="wallet")],
            [InlineKeyboardButton(get_text(lang, "profile_button"), callback_data="profile")],
            [InlineKeyboardButton(get_text(lang, "referral_button"), callback_data="referral")],
            [InlineKeyboardButton(get_text(lang, "change_lang_button"), callback_data="change_lang")],
            [InlineKeyboardButton(get_text(lang, "support_button"), url="https://t.me/otcgifttg/113382/113404")],
        ]

        # Пытаемся отправить баннер-картинку, если задан BANNER_FILE_ID
        if BANNER_FILE_ID:
            try:
                await context.bot.send_photo(
                    chat_id,
                    photo=BANNER_FILE_ID,
                    caption=get_text(lang, "start_message"),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            except Exception as e:
                logger.error(f"Ошибка отправки баннера: {e}")
                # Фолбэк — просто текст, чтобы не было «Произошла ошибка»
                await context.bot.send_message(
                    chat_id,
                    get_text(lang, "start_message"),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
        else:
            # Если баннер не задан — просто текстовое приветствие
            await context.bot.send_message(
                chat_id,
                get_text(lang, "start_message"),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        if chat_id:
            await context.bot.send_message(chat_id, "Произошла ошибка. Попробуйте позже.")


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /buy <deal_id> — альтернативный вход в сделку."""
    if not update.message:
        return
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    if not context.args:
        await update.message.reply_text("Использование: `/buy <ID_сделки>`", parse_mode="Markdown")
        return
    deal_id = context.args[0]
    await join_deal(user_id, chat_id, deal_id, context)


# ---------------------- CALLBACK-КНОПКИ ----------------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    ensure_user_exists(user_id)
    lang = user_data.get(user_id, {}).get("lang", "ru")

    try:
        # продавец сообщил, что отправил подарки
        if data.startswith("seller_sent_"):
            deal_id = data.split("_")[-1]

            await query.edit_message_text(
                "✅ Спасибо! Мы передадим информацию в поддержку.\n\n"
                f"Если вы ещё не отправили NFT-подарок(и) в {SUPPORT_USERNAME}, обязательно сделайте это."
            )

            target_chat = SUPPORT_CHAT_ID if SUPPORT_CHAT_ID != 0 else ADMIN_ID
            seller_username = query.from_user.username or query.from_user.id
            notify_text = (
                f"🎁 Продавец @{seller_username} нажал кнопку «Я отправил-(а)» "
                f"по сделке #{deal_id}."
            )
            try:
                await context.bot.send_message(
                    target_chat,
                    notify_text,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "✅ Подтвердить получение",
                                    callback_data=f"worker_confirm:{deal_id}:{query.from_user.id}",
                                )
                            ]
                        ]
                    ),
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления поддержке: {e}")
            return

        # воркер подтверждает получение подарка
        if data.startswith("worker_confirm:"):
            try:
                _, deal_id, seller_id_str = data.split(":")
                seller_id = int(seller_id_str)
            except Exception:
                await query.edit_message_text("Ошибка формата ID сделки.")
                return

            await query.edit_message_text(f"✅ Получение по сделке #{deal_id} подтверждено.")

            seller_lang = user_data.get(seller_id, {}).get("lang", "ru")
            if seller_lang == "ru":
                msg = (
                    f"✅ Покупатель подтвердил получение подарка по сделке #{deal_id}.\n\n"
                    "Денежные средства будут зачислены в течении 10-15 минут."
                )
            else:
                msg = (
                    f"✅ Buyer confirmed the gift for deal #{deal_id}.\n\n"
                    "Expect funds to be credited within 5-10 minutes."
                )

            try:
                await context.bot.send_message(seller_id, msg)
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения продавцу: {e}")
            return


        
        # смена языка
        if data.startswith("lang_"):
            new_lang = data.split("_")[-1]
            user_data[user_id]["lang"] = new_lang
            save_user_data(user_id)
            await query.edit_message_text(get_text(new_lang, "lang_set_message"))
            await start(update, context)
            return

        # профиль
        if data == "profile":
            usr = user_data.get(user_id, {})
            username = query.from_user.username or "None"
            sold_summary = get_sold_summary(user_id, lang)

            text = get_text(
                lang,
                "profile_message",
                user_id=user_id,
                username=username,
                successful_deals=usr.get("successful_deals", 0),
                balance=usr.get("balance", 0.0),
                valute=VALUTE,
                wallet=usr.get("wallet", "Не указан"),
                sold_summary=sold_summary,
            )

            await context.bot.send_message(
                chat_id,
                text,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]
                ),
            )
            return


# удалено дублирование профиля ниже (fix), НЕ редактируем фото
            await context.bot.send_message(
                chat_id,
                text,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]
                ),
            )
            return


        # управление постоянными кошельками
        if data == "wallet":
            # показываем все сохранённые реквизиты (если есть)
            saved_list = []
            uw = user_wallets.get(user_id, {})
            if "ton" in uw:
                saved_list.append(f"TON: {uw['ton']}")
            if "sbp" in uw:
                saved_list.append(f"СБП: {uw['sbp']}")
            if "card_rf" in uw:
                saved_list.append(f"Карта РФ: {uw['card_rf']}")
            if "card_ua" in uw:
                saved_list.append(f"Карта UA: {uw['card_ua']}")
            if "stars" in uw:
                saved_list.append(f"STARS: {uw['stars']}")

            info_text = "\n\n".join(saved_list) if saved_list else "У вас пока нет сохранённых реквизитов."

            await context.bot.send_message(
                chat_id,
                get_text(lang, "wallet_select_message") + "\n\n" + info_text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("💎 Добавить TON-кошелек", callback_data="wallet_ton")],
                        [InlineKeyboardButton("📱 Добавить СБП", callback_data="wallet_sbp")],
                        [InlineKeyboardButton("💳 Добавить банковскую карту (РФ)", callback_data="wallet_card_rf")],
                        [InlineKeyboardButton("💳 Добавить банковскую карту (UA)", callback_data="wallet_card_ua")],
                        [InlineKeyboardButton("⭐ Оплата в STARS", callback_data="wallet_stars")],
                        [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")],
                    ]
                ),
            )
            return

        if data in ("wallet_ton", "wallet_sbp", "wallet_card_rf", "wallet_card_ua", "wallet_stars"):
            wallet_type_map = {
                "wallet_ton": "TON-кошелька",
                "wallet_sbp": "СБП",
                "wallet_card_rf": "банковской карты (РФ)",
                "wallet_card_ua": "банковской карты (UA)",
                "wallet_stars": "STARS",
            }
            wallet_type = wallet_type_map.get(data, "кошелька")
            context.user_data["awaiting_wallet"] = True
            context.user_data["wallet_type"] = wallet_type
            await query.edit_message_text(get_text(lang, "wallet_type_prompt", wallet_type=wallet_type))
            return

        # выбор реквизитов и валюты ДЛЯ КОНКРЕТНОЙ СДЕЛКИ
        if data in DEAL_WALLET_TYPE_MAP:
            wallet_type = DEAL_WALLET_TYPE_MAP[data]
            deal_valute = DEAL_VALUTE_MAP.get(data, VALUTE)
            wallet_code = WALLET_CODE_MAP.get(wallet_type)

            saved_wallet = get_user_wallet(user_id, wallet_code) if wallet_code else None
            context.user_data["deal_valute"] = deal_valute

            if saved_wallet:
                # используем сохранённые реквизиты, сразу спрашиваем сумму
                context.user_data["deal_wallet"] = saved_wallet
                context.user_data["awaiting_amount"] = True
                await query.edit_message_text(
                    get_text(lang, "create_deal_message", valute=deal_valute),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]
                    ),
                )
            else:
                # просим ввести реквизиты и параллельно сохраним
                context.user_data["deal_wallet_type"] = wallet_type
                context.user_data["deal_wallet_code"] = wallet_code
                context.user_data["awaiting_deal_wallet"] = True
                await query.edit_message_text(get_text(lang, "wallet_type_prompt", wallet_type=wallet_type))
            return

        # запуск создания сделки
        if data == "create_deal":
            await context.bot.send_message(
                chat_id,
                get_text(lang, "wallet_select_message"),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("💎 TON", callback_data="deal_wallet_ton")],
                        [InlineKeyboardButton("📱 СБП", callback_data="deal_wallet_sbp")],
                        [InlineKeyboardButton("💳 Банковская карта (РФ)", callback_data="deal_wallet_card_rf")],
                        [InlineKeyboardButton("💳 Банковская карта (UA)", callback_data="deal_wallet_card_ua")],
                        [InlineKeyboardButton("⭐ STARS", callback_data="deal_wallet_stars")],
                        [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")],
                    ]
                ),
            )
            context.user_data["deal_creation"] = True
            return

        if data == "referral":
            referral_link = f"https://t.me/astralgarant_bot?start={user_id}"
            await context.bot.send_message(
                chat_id,
                get_text(lang, "referral_message", referral_link=referral_link, valute=VALUTE),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]
                ),
            )
            return

        if data == "change_lang":
            await context.bot.send_message(
                chat_id,
                get_text(lang, "change_lang_message"),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(get_text(lang, "english_lang_button"), callback_data="lang_en")],
                        [InlineKeyboardButton(get_text(lang, "russian_lang_button"), callback_data="lang_ru")],
                    ]
                ),
            )
            return

        if data == "menu":
            await start(update, context)
            return

        # --- админка ---
        if data == "admin_view_deals" and user_id == ADMIN_ID:
            if not deals:
                await context.bot.send_message(chat_id, "Нет активных сделок.")
            else:
                deals_list = "\n".join(
                    f"Сделка {d_id}: {d['amount']} {d.get('valute', VALUTE)}, Продавец: {d['seller_id']}"
                    for d_id, d in deals.items()
                )
                await context.bot.send_message(
                    chat_id,
                    get_text(lang, "admin_view_deals_message", deals_list=deals_list),
                )
            return

        if data == "admin_change_balance" and user_id == ADMIN_ID:
            await query.edit_message_text(get_text(lang, "admin_change_balance_message"))
            admin_commands[user_id] = "change_balance"
            return

        if data == "admin_change_successful_deals" and user_id == ADMIN_ID:
            await query.edit_message_text(get_text(lang, "admin_change_successful_deals_message"))
            admin_commands[user_id] = "change_successful_deals"
            return

        if data == "admin_change_valute" and user_id == ADMIN_ID:
            await query.edit_message_text(get_text(lang, "admin_change_valute_message"))
            admin_commands[user_id] = "change_valute"
            return

        # воркер: правка успешных сделок
        if data == "worker_change_deals" and user_id in WORKERS:
            await query.edit_message_text("Введите количество успешных сделок, которое хотите себе установить:")
            admin_commands[user_id] = "worker_change_successful_deals"
            return

        # оплата сделки
        if data.startswith("pay_from_balance_"):
            deal_id = data.split("_")[-1]
            deal = deals.get(deal_id)
            if not deal:
                await context.bot.send_message(chat_id, "Сделка не найдена.")
                return

            buyer_id = user_id
            seller_id = deal["seller_id"]
            amount = deal["amount"]
            valute = deal.get("valute", VALUTE)

            ensure_user_exists(buyer_id)
            ensure_user_exists(seller_id)

            # воркер — бесконечный баланс, списания нет
            if buyer_id in WORKERS:
                user_data[seller_id]["balance"] += amount
                save_user_data(seller_id)
            else:
                if user_data[buyer_id]["balance"] < amount:
                    await context.bot.send_message(
                        chat_id,
                        get_text(lang, "insufficient_balance_message"),
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]
                        ),
                    )
                    return
                user_data[buyer_id]["balance"] -= amount
                user_data[seller_id]["balance"] += amount
                save_user_data(buyer_id)
                save_user_data(seller_id)

            # фиксация продажи для профиля продавца
            record_sold_nft(seller_id, deal_id, amount, valute, deal["description"])

            # уведомление покупателю (только об оплате, сделка ещё не завершена)
            await context.bot.send_message(
                chat_id,
                get_text(
                    lang,
                    "payment_confirmed_message",
                    deal_id=deal_id,
                    amount=amount,
                    valute=valute,
                    description=deal["description"],
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]
                ),
            )

            # уведомление продавцу
            buyer_chat = await context.bot.get_chat(buyer_id)
            buyer_username = buyer_chat.username or "None"
            seller_lang = user_data.get(seller_id, {}).get("lang", "ru")
            await context.bot.send_message(
                seller_id,
                get_text(
                    seller_lang,
                    "payment_confirmed_seller_message",
                    deal_id=deal_id,
                    description=deal["description"],
                    buyer_username=buyer_username,
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "✅ Я отправил-(а)", callback_data=f"seller_sent_{deal_id}"
                            )
                        ]
                    ]
                ),
            )

            # увеличиваем успешные сделки продавца
            user_data[seller_id]["successful_deals"] += 1
            save_user_data(seller_id)

            # сделку из БД пока не удаляем — ID нужен в истории проданных NFT и до финального подтверждения
            return

    except Exception as e:
        logger.error(f"Ошибка в button: {e}")
        await context.bot.send_message(chat_id, "Произошла ошибка. Попробуйте позже.")


# ---------------------- ОБРАБОТКА ТЕКСТА ----------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global VALUTE
        if not update.message:
            return

        user_id = update.message.from_user.id
        text = update.message.text.strip()
        ensure_user_exists(user_id)
        lang = user_data.get(user_id, {}).get("lang", "ru")

        # --- команды админа ---
        if user_id == ADMIN_ID and admin_commands.get(user_id) == "change_balance":
            try:
                target_user_id_str, new_balance_str = map(str.strip, text.split())
                target_user_id = int(target_user_id_str)
                new_balance = float(new_balance_str)
                ensure_user_exists(target_user_id)
                user_data[target_user_id]["balance"] = new_balance
                save_user_data(target_user_id)
                await update.message.reply_text(
                    f"Баланс пользователя {target_user_id} изменен на {new_balance} {VALUTE}."
                )
            except Exception:
                await update.message.reply_text(
                    "Неверный формат. Введите ID пользователя и баланс через пробел."
                )
            admin_commands[user_id] = None
            return

        if user_id == ADMIN_ID and admin_commands.get(user_id) == "change_successful_deals":
            try:
                target_user_id_str, new_cnt_str = map(str.strip, text.split())
                target_user_id = int(target_user_id_str)
                new_cnt = int(new_cnt_str)
                ensure_user_exists(target_user_id)
                user_data[target_user_id]["successful_deals"] = new_cnt
                save_user_data(target_user_id)
                await update.message.reply_text(
                    f"Количество успешных сделок пользователя {target_user_id} изменено на {new_cnt}."
                )
            except Exception:
                await update.message.reply_text(
                    "Неверный формат. Введите ID пользователя и количество успешных сделок через пробел."
                )
            admin_commands[user_id] = None
            return

        if user_id == ADMIN_ID and admin_commands.get(user_id) == "change_valute":
            VALUTE = text.upper()
            await update.message.reply_text(f"Валюта по умолчанию изменена на {VALUTE}.")
            admin_commands[user_id] = None
            return

        # --- воркер меняет свои успешные сделки через панель ---
        if user_id in WORKERS and admin_commands.get(user_id) == "worker_change_successful_deals":
            try:
                new_cnt = int(text)
                user_data[user_id]["successful_deals"] = max(0, new_cnt)
                save_user_data(user_id)
                await update.message.reply_text(
                    f"Количество успешных сделок установлено на {new_cnt}."
                )
            except Exception:
                await update.message.reply_text("Неверный формат. Введите просто число, например: 15")
            admin_commands[user_id] = None
            return

        # --- создание сделки: ввод реквизитов (ОДНОРАЗОВЫХ) ---
        if context.user_data.get("awaiting_deal_wallet"):
            wallet_type = context.user_data.get("deal_wallet_type", "кошелька")
            wallet_code = context.user_data.get("deal_wallet_code")
            deal_wallet_value = f"{wallet_type}: {text}"
            context.user_data["deal_wallet"] = deal_wallet_value
            context.user_data["awaiting_deal_wallet"] = False

            # сохраняем как постоянные реквизиты для этого метода
            if wallet_code:
                save_user_wallet(user_id, wallet_code, deal_wallet_value)

            deal_valute = context.user_data.get("deal_valute", VALUTE)

            context.user_data["awaiting_amount"] = True
            await update.message.reply_text(
                get_text(lang, "create_deal_message", valute=deal_valute),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]
                ),
            )
            return

        # --- создание сделки: ввод суммы ---
        if context.user_data.get("awaiting_amount"):
            try:
                amount = float(text.replace(",", "."))
                context.user_data["amount"] = amount
                context.user_data["awaiting_amount"] = False
                context.user_data["awaiting_description"] = True
                await update.message.reply_text(
                    get_text(lang, "awaiting_description_message"),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]
                    ),
                )
            except ValueError:
                await update.message.reply_text("Неверный формат. Введите число, например 100 или 100.5")
            return

        # --- создание сделки: ссылки на NFT и финальное сохранение ---
        if context.user_data.get("awaiting_description"):
            parts = text.split()
            links = [part for part in parts if URL_REGEX.match(part)]

            if not links:
                if lang == "ru":
                    msg = (
                        "❌ В этом боте можно продавать только NFT-подарки.\n\n"
                        "Отправьте ссылку или несколько ссылок на NFT-подарок(и).\n"
                        "Пример:\n"
                        "https://t.me/nft/Example-1"
                    )
                else:
                    msg = (
                        "❌ This bot is only for NFT gifts.\n\n"
                        "Please send one or more NFT links.\n"
                        "Example:\n"
                        "https://t.me/nft/Example-1"
                    )
                await update.message.reply_text(msg)
                return

            description_links = "\n".join(links)

            deal_id = generate_deal_id()
            amount = context.user_data.get("amount", 0.0)
            deal_wallet = context.user_data.get(
                "deal_wallet", user_data.get(user_id, {}).get("wallet", "Не указан")
            )
            deal_valute = context.user_data.get("deal_valute", VALUTE)

            deals[deal_id] = {
                "amount": amount,
                "description": description_links,
                "seller_id": user_id,
                "buyer_id": None,
                "wallet": deal_wallet,
                "valute": deal_valute,
            }
            save_deal(deal_id)
            context.user_data.clear()

            await update.message.reply_text(
                get_text(
                    lang,
                    "deal_created_message",
                    amount=amount,
                    valute=deal_valute,
                    description=description_links,
                    deal_link=f"https://t.me/astralgarant_bot?start={deal_id}",
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]
                ),
            )

            await context.bot.send_message(
                ADMIN_ID,
                f"Новая сделка создана:\nID: {deal_id}\nСумма: {amount} {deal_valute}\nПродавец: {user_id}",
            )
            return

        # --- постоянный кошелёк пользователя ---
        if context.user_data.get("awaiting_wallet"):
            try:
                wallet_type = context.user_data.pop("wallet_type", None)
                if wallet_type:
                    wallet_value = f"{wallet_type}: {text}"
                else:
                    wallet_value = text
                user_data[user_id]["wallet"] = wallet_value
                save_user_data(user_id)
                context.user_data.pop("awaiting_wallet", None)

                # сохраняем в таблицу user_wallets, если тип известен
                wallet_code = WALLET_CODE_MAP.get(wallet_type)
                if wallet_code:
                    save_user_wallet(user_id, wallet_code, wallet_value)

                await update.message.reply_text(
                    get_text(lang, "wallet_updated_message", wallet=wallet_value),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]
                    ),
                )
            except Exception as e:
                logger.error(f"Ошибка при обновлении кошелька: {e}")
                await update.message.reply_text("Произошла ошибка. Попробуйте ещё раз.")
            return

    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        if update.message:
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")


# ---------------------- ЗАПУСК ----------------------
def main() -> None:
    init_db()
    load_data()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("astralteam", worker_login))
    application.add_handler(CommandHandler("deals", worker_set_deals))
    application.add_handler(CommandHandler("buy", buy))

    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()


if __name__ == "__main__":
    main()
