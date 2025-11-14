# Тексты на русском языке
RU_TEXTS = {
    "start_message": (
        "Добро пожаловать в Astral OTC – надежный P2P-гарант\n\n"
        "💼 Покупайте и продавайте всё, что угодно – безопасно!\n"
        "От Telegram-подарков и NFT до токенов и фиата – сделки проходят легко и без риска.\n\n"
        "🔹 Удобное управление кошельками\n"
        "🔹 Реферальная система\n\n"
        "📖 Как пользоваться?\n"
        "Ознакомьтесь с инструкцией — https://telegra.ph/Astral-P2P-Guarantor--Instrukciya-11-14\n"
        "Выберите нужный раздел ниже:"
    ),

    "wallet_message": (
        "💼 Ваш текущий кошелек: {wallet}\n\n"
        "Отправьте новые реквизиты кошелька для изменения или нажмите кнопку ниже для возврата в меню."
    ),

    "wallet_select_message": (
        "💼 Добавьте ваш способ оплаты:\n\n"
        "Пожалуйста, выберите тип кошелька ниже:"
    ),

    "wallet_type_prompt": (
        "Пожалуйста, введите реквизиты для {wallet_type}:"
    ),

    "create_deal_message": (
        "💼 Создание сделки\n\n"
        "Введите сумму {valute} сделки в формате: 100.5"
    ),

    "referral_message": (
        "🔗 Ваша реферальная ссылка:\n{referral_link}\n\n"
        "👥 Количество рефералов: 0\n"
        "💰 Заработано с рефералов: 0 {valute}\n"
        "40% от комиссии бота"
    ),

    "change_lang_message": (
        "🌍 Выберите язык:\n\n"
        "Выберите язык:"
    ),

    "lang_set_message": "Язык изменен на русский.",

    "deal_created_message": (
        "✅ Сделка успешно создана!\n\n"
        "💰 Сумма: {amount} {valute}\n"
        "🎁 NFT-подарок(и):\n{description}\n\n"
        "🔗 Ссылка для покупателя: {deal_link}"
    ),

    "payment_confirmed_message": (
        "✅ Оплата принята по сделке #{deal_id}\n\n"
        "💰 Сумма: {amount} {valute}\n"
        "🎁 NFT-подарок(и):\n{description}\n\n"
        "Ожидайте, пока продавец отправит подарок."
    ),

    "payment_confirmed_seller_message": (
        "✅ Оплата подтверждена для сделки #{deal_id}\n\n"
        "Теперь необходимо отправить NFT-подарок(и) в поддержку @astral_helper.\n\n"
        "После того как вы полностью отправите все подарки в поддержку, "
        "нажмите кнопку «Я отправил-(а)» под этим сообщением."
    ),

    "seller_notification_message": (
        "Пользователь @{buyer_username} присоединился к сделке #{deal_id}\n"
        "• Успешные сделки: {successful_deals}\n\n"
        "⚠️ Проверьте, что это тот же пользователь, с которым вы вели диалог ранее!"
    ),

    "insufficient_balance_message": "❌ Недостаточно средств на балансе!",

    "wallet_updated_message": "💼 Ваш кошелёк обновлен: {wallet}",

    "admin_panel_message": "Админ-панель:",
    "admin_view_deals_message": "Активные сделки:\n{deals_list}",
    "admin_change_balance_message": "Введите ID пользователя и новый баланс в формате: user_id баланс",
    "admin_change_successful_deals_message": "Введите ID пользователя и количество успешных сделок в формате: user_id количество",
    "admin_change_valute_message": "Введите новую валюту (например, USD, EUR, RUB):",

    "menu_button": "🔙Вернуться в меню",
    "pay_from_balance_button": "✅ Подтвердить оплату",
    "add_wallet_button": "🪙Добавить/изменить кошелёк",
    "create_deal_button": "📄Создать сделку",
    "profile_button": "👤Профиль",
    "referral_button": "🧷Реферальная ссылка",
    "change_lang_button": "🌐Change language",
    "support_button": "📞Поддержка",
    "english_lang_button": "English",
    "russian_lang_button": "Русский",

    "admin_view_deals_button": "Просмотр сделок",
    "admin_change_balance_button": "Изменить баланс пользователя",
    "admin_change_successful_deals_button": "Изменить успешные сделки",
    "admin_change_valute_button": "Изменить валюту",

    "deal_info_message": (
        "📄 Информация о сделке #{deal_id}\n\n"
        "Вы покупатель в сделке.\n"
        "Продавец: @{seller_username}\n"
        "Успешные сделки: {successful_deals}\n\n"
        "Сумма сделки: {amount} {valute}\n\n"
        "Вы покупаете:\n"
        "{description}\n\n"
        "Адрес для оплаты:\n"
        "{wallet}\n\n"
        "Комментарий к платежу (мемо): {deal_id}\n\n"
        "⚠️ Пожалуйста, убедитесь в правильности данных перед оплатой.\n"
        "Комментарий (мемо) обязателен!\n\n"
        "После оплаты ожидайте автоматического подтверждения."
    ),

    "awaiting_description_message": (
        "🔗 Укажите ссылку или ссылки на NFT-подарок(и), которые вы продаёте:\n\n"
        "Пример: https://t.me/nft/Example-1"
    ),

    "profile_message": (
        "👤 Профиль Astral\n\n"
        "ID: {user_id}\n"
        "Юзернейм: @{username}\n"
        "Успешные сделки: {successful_deals}\n"
        "Баланс: {balance} {valute}\n"
        "Текущий кошелёк: {wallet}\n\n"
        "Проданные NFT:\n{sold_summary}"
    ),
}

# Тексты на английском языке
EN_TEXTS = {
    # (оставил без изменений)
}

# Функция получения текста
def get_text(lang, key, **kwargs):
    if lang == "ru":
        return RU_TEXTS.get(key, "").format(**kwargs)
    elif lang == "en":
        return EN_TEXTS.get(key, "").format(**kwargs)
    return ""
