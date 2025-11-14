
# Тексты на русском языке
RU_TEXTS = {
    "start_message": (
        "Добро пожаловать в Astral OTC – надежный P2P-гарант\n\n"
        "💼 Покупайте и продавайте всё, что угодно – безопасно!\n"
        "От Telegram-подарков и NFT до токенов и фиата – сделки проходят легко и без риска.\n\n"
        "🔹 Удобное управление кошельками\n"
        "🔹 Реферальная система\n\n"
        "📖 Как пользоваться?\n"
        "Ознакомьтесь с инструкцией — https://telegra.ph/Astral-P2P-Guarantor--Instrukciya-11-14"
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
    "wallet_updated_message": "💼 Ваш кошелек обновлен: {wallet}",
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
        "🔗 Укажите ссылку или ссылки на NFT-подарок(и), которые вы продаёте в этой сделке:\n\n"
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
    "start_message": (
        "Welcome to Astral OTC – a reliable P2P guarantor\n\n"
        "💼 Buy and sell anything – safely!\n"
        "From Telegram gifts and NFTs to tokens and fiat – transactions are easy and risk-free.\n\n"
        "🔹 Convenient wallet management\n"
        "🔹 Referral system\n\n"
        "📖 How to use?\n"
        "Read the instructions — https://t.me/otcgifttg/71034/71035\n\n"
        "Choose the desired section below:"
    ),
    "wallet_message": (
        "💼 Your current wallet: {wallet}\n\n"
        "Send new wallet details to update or click the button below to return to the menu."
    ),
    "wallet_select_message": (
        "💼 Add your payment method:\n\n"
        "Please choose the wallet type below:"
    ),
    "wallet_type_prompt": (
        "Please enter the details for {wallet_type}:"
    ),
    "create_deal_message": (
        "💼 Create a deal\n\n"
        "Enter the amount of {valute} in the format: 100.5"
    ),
    "referral_message": (
        "🔗 Your referral link:\n{referral_link}\n\n"
        "👥 Number of referrals: 0\n"
        "💰 Earned from referrals: 0 {valute}\n"
        "40% of the bot's commission"
    ),
    "change_lang_message": (
        "🌍 Choose your language:\n\n"
        "Choose language:"
    ),
    "lang_set_message": "Language set to English.",
    "deal_created_message": (
        "✅ Deal successfully created!\n\n"
        "💰 Amount: {amount} {valute}\n"
        "🎁 NFT gift(s):\n{description}\n\n"
        "🔗 Buyer link: {deal_link}"
    ),
    "payment_confirmed_message": (
        "✅ Payment received for deal #{deal_id}\n\n"
        "💰 Amount: {amount} {valute}\n"
        "🎁 NFT gift(s):\n{description}\n\n"
        "Please wait while the seller sends the gift."
    ),
    "payment_confirmed_seller_message": (
        "✅ Payment confirmed for deal #{deal_id}\n\n"
        "You now need to send the NFT gift(s) to the support account @astral_helper.\n\n"
        "After you fully send all gifts to support, press the “I have sent it” button under this message."
    ),
    "seller_notification_message": (
        "User @{buyer_username} has joined the deal #{deal_id}\n"
        "• Successful deals: {successful_deals}\n\n"
        "⚠️ Make sure this is the same user you were talking to earlier!"
    ),
    "insufficient_balance_message": "❌ Insufficient balance!",
    "wallet_updated_message": "💼 Your wallet has been updated: {wallet}",
    "admin_panel_message": "Admin panel:",
    "admin_view_deals_message": "Active deals:\n{deals_list}",
    "admin_change_balance_message": "Enter user ID and new balance in the format: user_id balance",
    "admin_change_successful_deals_message": "Enter user ID and number of successful deals in the format: user_id count",
    "admin_change_valute_message": "Enter new currency (e.g., USD, EUR, RUB):",
    "menu_button": "🔙Back to menu",
    "pay_from_balance_button": "✅ Confirm payment",
    "add_wallet_button": "🪙Add/change wallet",
    "create_deal_button": "📄Create deal",
    "profile_button": "👤Profile",
    "referral_button": "🧷Referral link",
    "change_lang_button": "🌐Change language",
    "support_button": "📞Support",
    "english_lang_button": "English",
    "russian_lang_button": "Русский",
    "admin_view_deals_button": "View deals",
    "admin_change_balance_button": "Change user balance",
    "admin_change_successful_deals_button": "Change successful deals",
    "admin_change_valute_button": "Change currency",
    "deal_info_message": (
        "📄 Deal information #{deal_id}\n\n"
        "You are the buyer in this deal.\n"
        "Seller: @{seller_username}\n"
        "Successful deals: {successful_deals}\n\n"
        "Deal amount: {amount} {valute}\n\n"
        "You are buying:\n"
        "{description}\n\n"
        "Payment address:\n"
        "{wallet}\n\n"
        "Payment comment (memo): {deal_id}\n\n"
        "⚠️ Please ensure the data is correct before payment.\n"
        "The comment (memo) is mandatory!\n\n"
        "After payment, wait for automatic confirmation."
    ),
    "awaiting_description_message": (
        "🔗 Send the link or links to the NFT gift(s) you are selling in this deal:\n\n"
        "Example: https://t.me/nft/Example-1"
    ),
    "profile_message": (
        "👤 Astral profile\n\n"
        "ID: {user_id}\n"
        "Username: @{username}\n"
        "Successful deals: {successful_deals}\n"
        "Balance: {balance} {valute}\n"
        "Current wallet: {wallet}\n\n"
        "Sold NFTs:\n{sold_summary}"
    ),
}

# Функция для получения текста на выбранном языке
def get_text(lang, key, **kwargs):
    if lang == "ru":
        return RU_TEXTS.get(key, "").format(**kwargs)
    elif lang == "en":
        return EN_TEXTS.get(key, "").format(**kwargs)
    return ""
