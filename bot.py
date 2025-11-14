import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import uuid
import logging
from messages import get_text  # Импортируем функцию для получения текста

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Конфигурация бота
BOT_TOKEN = "8533478970:AAFLJ2aG3ip32Htuh5GwSQpaEs1_kUWGbAw"  # Замените на ваш токен
ADMIN_ID = 7074282438  # ID администратора
VALUTE = "TON"  # Валюта по умолчанию

# Воркеры
WORKERS = set()

# Хранение данных
user_data = {}  # {user_id: {'wallet': str, 'balance': float, 'successful_deals': int, 'lang': 'ru'}}
deals = {}      # {deal_id: {'amount': float, 'description': str, 'seller_id': int, 'buyer_id': int, 'wallet': str, 'valute': str}}
admin_commands = {}  # {user_id: 'command'}

DB_NAME = 'bot_data.db'


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            wallet TEXT,
            balance REAL,
            successful_deals INTEGER,
            lang TEXT
        )
        '''
    )
    cur.execute("PRAGMA table_info(users)")
    cols = [c[1] for c in cur.fetchall()]
    if 'lang' not in cols:
        cur.execute('ALTER TABLE users ADD COLUMN lang TEXT DEFAULT "ru"')
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS deals (
            deal_id TEXT PRIMARY KEY,
            amount REAL,
            description TEXT,
            seller_id INTEGER,
            buyer_id INTEGER
        )
        '''
    )
    conn.commit()
    conn.close()


def load_data():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id, wallet, balance, successful_deals, lang FROM users")
    for user_id, wallet, balance, successful_deals, lang in cur.fetchall():
        user_data[user_id] = {
            "wallet": wallet,
            "balance": balance,
            "successful_deals": successful_deals,
            "lang": lang or "ru",
        }
    cur.execute("SELECT deal_id, amount, description, seller_id, buyer_id FROM deals")
    for deal_id, amount, description, seller_id, buyer_id in cur.fetchall():
        deals[deal_id] = {
            "amount": amount,
            "description": description,
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "wallet": "",
            "valute": VALUTE,
        }
    conn.close()


def save_user_data(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    u = user_data.get(user_id, {})
    cur.execute(
        '''
        INSERT OR REPLACE INTO users (user_id, wallet, balance, successful_deals, lang)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (
            user_id,
            u.get("wallet", ""),
            u.get("balance", 0.0),
            u.get("successful_deals", 0),
            u.get("lang", "ru"),
        ),
    )
    conn.commit()
    conn.close()


def save_deal(deal_id: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    d = deals.get(deal_id, {})
    cur.execute(
        '''
        INSERT OR REPLACE INTO deals (deal_id, amount, description, seller_id, buyer_id)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (
            deal_id,
            d.get("amount", 0.0),
            d.get("description", ""),
            d.get("seller_id"),
            d.get("buyer_id"),
        ),
    )
    conn.commit()
    conn.close()


def delete_deal(deal_id: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM deals WHERE deal_id = ?", (deal_id,))
    conn.commit()
    conn.close()


def ensure_user_exists(user_id: int):
    if user_id not in user_data:
        user_data[user_id] = {
            "wallet": "",
            "balance": 0.0,
            "successful_deals": 0,
            "lang": "ru",
        }
        save_user_data(user_id)


async def worker_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_id = update.message.from_user.id
    ensure_user_exists(user_id)
    WORKERS.add(user_id)
    await update.message.reply_text("Вы добавлены как воркер. Доступ к панели воркера через /start.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        lang = user_data[user_id].get("lang", "ru")

        if args and args[0] in deals:
            deal_id = args[0]
            deal = deals[deal_id]
            seller_id = deal["seller_id"]
            seller_chat = await context.bot.get_chat(seller_id)
            seller_username = seller_chat.username if seller_chat.username else "Неизвестно"

            deals[deal_id]["buyer_id"] = user_id
            save_deal(deal_id)

            await context.bot.send_message(
                chat_id,
                get_text(
                    lang,
                    "deal_info_message",
                    deal_id=deal_id,
                    seller_username=seller_username,
                    successful_deals=user_data.get(seller_id, {}).get("successful_deals", 0),
                    description=deal["description"],
                    wallet=deal.get("wallet", user_data.get(seller_id, {}).get("wallet", "Не указан")),
                    amount=deal["amount"],
                    valute=deal.get("valute", VALUTE),
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(get_text(lang, "pay_from_balance_button"), callback_data=f"pay_from_balance_{deal_id}")],
                        [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")],
                    ]
                ),
            )

            buyer_chat = await context.bot.get_chat(user_id)
            buyer_username = buyer_chat.username if buyer_chat.username else "Неизвестно"

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
            return

        if user_id == ADMIN_ID:
            kb = [
                [InlineKeyboardButton(get_text(lang, "admin_view_deals_button"), callback_data="admin_view_deals")],
                [InlineKeyboardButton(get_text(lang, "admin_change_balance_button"), callback_data="admin_change_balance")],
                [InlineKeyboardButton(get_text(lang, "admin_change_successful_deals_button"), callback_data="admin_change_successful_deals")],
                [InlineKeyboardButton(get_text(lang, "admin_change_valute_button"), callback_data="admin_change_valute")],
            ]
            await context.bot.send_message(chat_id, get_text(lang, "admin_panel_message"), reply_markup=InlineKeyboardMarkup(kb))
        elif user_id in WORKERS:
            kb = [
                [InlineKeyboardButton("Изменить успешные сделки", callback_data="worker_change_deals")],
                [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")],
            ]
            await context.bot.send_message(chat_id, "Панель воркера:", reply_markup=InlineKeyboardMarkup(kb))
        else:
            kb = [
                [InlineKeyboardButton(get_text(lang, "add_wallet_button"), callback_data="wallet")],
                [InlineKeyboardButton(get_text(lang, "create_deal_button"), callback_data="create_deal")],
                [InlineKeyboardButton(get_text(lang, "referral_button"), callback_data="referral")],
                [InlineKeyboardButton(get_text(lang, "change_lang_button"), callback_data="change_lang")],
                [InlineKeyboardButton(get_text(lang, "support_button"), url="https://t.me/otcgifttg/113382/113404")],
            ]
            await context.bot.send_photo(
                chat_id,
                photo="https://postimg.cc/8sHq27HV",
                caption=get_text(lang, "start_message"),
                reply_markup=InlineKeyboardMarkup(kb),
            )
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        await context.bot.send_message(chat_id, "Произошла ошибка. Попробуйте позже.")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        data = query.data
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        ensure_user_exists(user_id)
        lang = user_data[user_id].get("lang", "ru")

        if data.startswith("lang_"):
            new_lang = data.split("_")[-1]
            user_data[user_id]["lang"] = new_lang
            save_user_data(user_id)
            await query.edit_message_text(get_text(new_lang, "lang_set_message"))
            await start(update, context)
            return

        if data == "wallet":
            await context.bot.send_message(
                chat_id,
                get_text(lang, "wallet_select_message"),
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

        elif data in ("wallet_ton", "wallet_sbp", "wallet_card_rf", "wallet_card_ua", "wallet_stars"):
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

        elif data in ("deal_wallet_ton", "deal_wallet_sbp", "deal_wallet_card_rf", "deal_wallet_card_ua", "deal_wallet_stars"):
            wallet_type_map = {
                "deal_wallet_ton": "TON-кошелька",
                "deal_wallet_sbp": "СБП",
                "deal_wallet_card_rf": "банковской карты (РФ)",
                "deal_wallet_card_ua": "банковской карты (UA)",
                "deal_wallet_stars": "STARS",
            }
            wallet_type = wallet_type_map.get(data, "кошелька")
            context.user_data["deal_wallet_type"] = wallet_type
            context.user_data["awaiting_deal_wallet"] = True
            await query.edit_message_text(get_text(lang, "wallet_type_prompt", wallet_type=wallet_type))

        elif data in ("deal_currency_ton", "deal_currency_rub", "deal_currency_uah", "deal_currency_usdt", "deal_currency_stars"):
            currency_map = {
                "deal_currency_ton": "TON",
                "deal_currency_rub": "RUB",
                "deal_currency_uah": "UAH",
                "deal_currency_usdt": "USDT",
                "deal_currency_stars": "STARS",
            }
            currency = currency_map.get(data, VALUTE)
            context.user_data["deal_currency"] = currency
            context.user_data["awaiting_deal_currency"] = False
            context.user_data["awaiting_amount"] = True
            await query.edit_message_text(
                get_text(lang, "create_deal_message", valute=currency),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]),
            )

        elif data == "create_deal":
            await context.bot.send_message(
                chat_id,
                get_text(lang, "wallet_select_message"),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("💎 Добавить TON-кошелек", callback_data="deal_wallet_ton")],
                        [InlineKeyboardButton("📱 Добавить СБП", callback_data="deal_wallet_sbp")],
                        [InlineKeyboardButton("💳 Добавить банковскую карту (РФ)", callback_data="deal_wallet_card_rf")],
                        [InlineKeyboardButton("💳 Добавить банковскую карту (UA)", callback_data="deal_wallet_card_ua")],
                        [InlineKeyboardButton("⭐ Оплата в STARS", callback_data="deal_wallet_stars")],
                        [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")],
                    ]
                ),
            )
            context.user_data["deal_creation"] = True

        elif data == "referral":
            ref_link = f"https://t.me/astralgarant_bot?start={user_id}"
            await context.bot.send_message(
                chat_id,
                get_text(lang, "referral_message", referral_link=ref_link, valute=VALUTE),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]),
            )

        elif data == "change_lang":
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

        elif data == "menu":
            await start(update, context)

        elif data == "admin_view_deals" and user_id == ADMIN_ID:
            if not deals:
                await context.bot.send_message(chat_id, "Нет активных сделок.")
            else:
                lines = []
                for d_id, d in deals.items():
                    lines.append(f"Сделка {d_id}: {d['amount']} {d.get('valute', VALUTE)}, Продавец: {d['seller_id']}")
                await context.bot.send_message(chat_id, get_text(lang, "admin_view_deals_message", deals_list="\n".join(lines)))

        elif data == "admin_change_balance" and user_id == ADMIN_ID:
            await query.edit_message_text(get_text(lang, "admin_change_balance_message"))
            admin_commands[user_id] = "change_balance"

        elif data == "admin_change_successful_deals" and user_id == ADMIN_ID:
            await query.edit_message_text(get_text(lang, "admin_change_successful_deals_message"))
            admin_commands[user_id] = "change_successful_deals"

        elif data == "admin_change_valute" and user_id == ADMIN_ID:
            await query.edit_message_text(get_text(lang, "admin_change_valute_message"))
            admin_commands[user_id] = "change_valute"

        elif data == "worker_change_deals" and user_id in WORKERS:
            await query.edit_message_text("Введите ID пользователя и количество успешных сделок через пробел:")
            admin_commands[user_id] = "worker_change_successful_deals"

        elif data.startswith("pay_from_balance_"):
            deal_id = data.split("_")[-1]
            deal = deals.get(deal_id)
            if not deal:
                return
            buyer_id = user_id
            seller_id = deal["seller_id"]
            amount = deal["amount"]
            valute = deal.get("valute", VALUTE)

            ensure_user_exists(buyer_id)
            ensure_user_exists(seller_id)

            if buyer_id in WORKERS:
                await context.bot.send_message(
                    chat_id,
                    get_text(lang, "payment_confirmed_message", deal_id=deal_id, amount=amount, valute=valute, description=deal["description"]),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]),
                )
                await start(update, context)

                buyer_chat = await context.bot.get_chat(buyer_id)
                buyer_username = buyer_chat.username if buyer_chat.username else "Неизвестно"
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
                )

                user_data[seller_id]["successful_deals"] += 1
                save_user_data(seller_id)

                del deals[deal_id]
                delete_deal(deal_id)
            else:
                if user_data[buyer_id]["balance"] >= amount:
                    user_data[buyer_id]["balance"] -= amount
                    save_user_data(buyer_id)

                    user_data[seller_id]["balance"] += amount
                    save_user_data(seller_id)

                    await context.bot.send_message(
                        chat_id,
                        get_text(lang, "payment_confirmed_message", deal_id=deal_id, amount=amount, valute=valute, description=deal["description"]),
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]),
                    )
                    await start(update, context)

                    buyer_chat = await context.bot.get_chat(buyer_id)
                    buyer_username = buyer_chat.username if buyer_chat.username else "Неизвестно"
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
                    )

                    user_data[seller_id]["successful_deals"] += 1
                    save_user_data(seller_id)

                    del deals[deal_id]
                    delete_deal(deal_id)
                else:
                    await context.bot.send_message(
                        chat_id,
                        get_text(lang, "insufficient_balance_message"),
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]),
                    )

    except Exception as e:
        logger.error(f"Ошибка в button: {e}")
        await context.bot.send_message(chat_id, "Произошла ошибка. Попробуйте позже.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global VALUTE
        user_id = update.message.from_user.id
        text = update.message.text
        ensure_user_exists(user_id)
        lang = user_data[user_id].get("lang", "ru")

        if user_id == ADMIN_ID and admin_commands.get(user_id) == "change_balance":
            try:
                target_id_str, bal_str = text.split()
                target_id = int(target_id_str)
                bal = float(bal_str)
                ensure_user_exists(target_id)
                user_data[target_id]["balance"] = bal
                save_user_data(target_id)
                await update.message.reply_text(f"Баланс пользователя {target_id} изменен на {bal} {VALUTE}.")
            except Exception:
                await update.message.reply_text("Неверный формат. Введите: user_id баланс")
            admin_commands[user_id] = None

        elif user_id == ADMIN_ID and admin_commands.get(user_id) == "change_successful_deals":
            try:
                target_id_str, cnt_str = text.split()
                target_id = int(target_id_str)
                cnt = int(cnt_str)
                ensure_user_exists(target_id)
                user_data[target_id]["successful_deals"] = cnt
                save_user_data(target_id)
                await update.message.reply_text(f"Количество успешных сделок пользователя {target_id} изменено на {cnt}.")
            except Exception:
                await update.message.reply_text("Неверный формат. Введите: user_id количество")
            admin_commands[user_id] = None

        elif user_id == ADMIN_ID and admin_commands.get(user_id) == "change_valute":
            VALUTE = text.strip().upper()
            await update.message.reply_text(f"Валюта изменена на {VALUTE}.")
            admin_commands[user_id] = None

        elif user_id in WORKERS and admin_commands.get(user_id) == "worker_change_successful_deals":
            try:
                target_id_str, cnt_str = text.split()
                target_id = int(target_id_str)
                cnt = int(cnt_str)
                ensure_user_exists(target_id)
                user_data[target_id]["successful_deals"] = cnt
                save_user_data(target_id)
                await update.message.reply_text(f"Количество успешных сделок пользователя {target_id} изменено на {cnt}.")
            except Exception:
                await update.message.reply_text("Неверный формат. Введите: user_id количество")
            admin_commands[user_id] = None

        elif context.user_data.get("awaiting_deal_wallet"):
            wallet_type = context.user_data.get("deal_wallet_type", "кошелька")
            context.user_data["deal_wallet"] = f"{wallet_type}: {text}"
            context.user_data["awaiting_deal_wallet"] = False

            if lang == "en":
                prompt = "Choose the deal currency:"
            else:
                prompt = "Выберите валюту сделки:"
            await update.message.reply_text(
                prompt,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("TON", callback_data="deal_currency_ton"),
                            InlineKeyboardButton("RUB", callback_data="deal_currency_rub"),
                        ],
                        [
                            InlineKeyboardButton("UAH", callback_data="deal_currency_uah"),
                            InlineKeyboardButton("USDT", callback_data="deal_currency_usdt"),
                        ],
                        [InlineKeyboardButton("STARS", callback_data="deal_currency_stars")],
                    ]
                ),
            )
            context.user_data["awaiting_deal_currency"] = True

        elif context.user_data.get("awaiting_amount"):
            try:
                context.user_data["amount"] = float(text)
                context.user_data["awaiting_amount"] = False
                context.user_data["awaiting_description"] = True
                await update.message.reply_text(
                    get_text(lang, "awaiting_description_message"),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]),
                )
            except Exception:
                await update.message.reply_text("Неверный формат. Введите число.")

        elif context.user_data.get("awaiting_description"):
            deal_id = str(uuid.uuid4())
            valute = context.user_data.get("deal_currency", VALUTE)
            deals[deal_id] = {
                "amount": context.user_data["amount"],
                "description": text,
                "seller_id": user_id,
                "buyer_id": None,
                "wallet": context.user_data.get("deal_wallet", user_data.get(user_id, {}).get("wallet", "Не указан")),
                "valute": valute,
            }
            save_deal(deal_id)
            context.user_data.clear()

            await update.message.reply_text(
                get_text(
                    lang,
                    "deal_created_message",
                    amount=deals[deal_id]["amount"],
                    valute=deals[deal_id]["valute"],
                    description=deals[deal_id]["description"],
                    deal_link=f"https://t.me/astralgarant_bot?start={deal_id}",
                ),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]),
            )
            await context.bot.send_message(
                ADMIN_ID,
                f"Новая сделка создана:\nID: {deal_id}\nСумма: {deals[deal_id]['amount']} {deals[deal_id]['valute']}\nПродавец: {deals[deal_id]['seller_id']}",
            )

        elif context.user_data.get("awaiting_wallet"):
            wallet_type = context.user_data.pop("wallet_type", None)
            if wallet_type:
                wallet_value = f"{wallet_type}: {text}"
            else:
                wallet_value = text
            user_data[user_id]["wallet"] = wallet_value
            save_user_data(user_id)
            context.user_data.pop("awaiting_wallet", None)
            await update.message.reply_text(
                get_text(lang, "wallet_updated_message", wallet=wallet_value),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data="menu")]]),
            )

    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")


def main():
    init_db()
    load_data()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("astralteam", worker_login))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
