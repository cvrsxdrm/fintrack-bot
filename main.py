import requests
import os
import telebot
from telebot import types
from config import EXCHANGE_KEY 
from config import TOKEN
from datetime import datetime

bot = telebot.TeleBot(TOKEN)
CURRENCIES = {"🪙 BTC": "bitcoin", "🔹 ETH": "ethereum", "USDT": "tether", "SOL": "solana", "BNB": "binancecoin", "XRP": "ripple", "USDC": "usd-coin", "ADA": "cardano", "DOGE": "dogecoin", "TRX": "tron"}
CATEGORIES = ["🍕 Еда", "🚌 Транспорт", "🎮 Развлечения"]

def main_menu_markup():

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton("💰 Криптовалюты", callback_data="crypto_menu"),
        types.InlineKeyboardButton("💸 Добавить расход", callback_data="add_spendings"),
        types.InlineKeyboardButton("📋 Посмотреть расходы", callback_data="read_spendings"),
        types.InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history"),
        types.InlineKeyboardButton("💳 Валюты", callback_data="check_money"))
    
    return markup

def get_fiat_rate(base="USD", target="RUB"):
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_KEY}/pair/{base}/{target}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('result') == 'success':
            return data['conversion_rate']
        return None
    except:
        return None

def get_price(coin_id, vs_currency="usd"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={vs_currency}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if coin_id in data and vs_currency in data[coin_id]:
            return data[coin_id][vs_currency]

        else:
            return None

    except requests.exceptions.RequestException:
        return None

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, "🌟 Привет!\n\n 💸 Я бот финансист, помогу тебе с финансами.", reply_markup = main_menu_markup())

# блок криптовалюты
@bot.callback_query_handler(func=lambda call: call.data == "crypto_menu")
def choose_currency(call):
    bot.answer_callback_query(call.id)

    markup = types.InlineKeyboardMarkup(row_width=2)

    for coin_name in CURRENCIES.keys():
        item = types.InlineKeyboardButton(text=coin_name, callback_data=f"crypto_{coin_name}")
        markup.add(item) 
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))

    bot.edit_message_text("📈 Выбери монету:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("crypto_"))
def ask_fiat_currency(call):
    bot.answer_callback_query(call.id)
    coin_name = call.data.split("_")[1]
    coin_id = CURRENCIES[coin_name]

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_usd = types.InlineKeyboardButton("💵 USD", callback_data=f"fiat_{coin_id}_usd")
    btn_eur = types.InlineKeyboardButton("💶 EUR", callback_data=f"fiat_{coin_id}_eur")
    btn_rub = types.InlineKeyboardButton("💳 RUB", callback_data=f"fiat_{coin_id}_rub")
    btn_jpy = types.InlineKeyboardButton("💴 JPY", callback_data=f"fiat_{coin_id}_jpy")

    markup.add(btn_usd, btn_eur, btn_rub, btn_jpy)

    bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id,text=f"В какой валюте показать курс {coin_name}?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("fiat_"))
def callback_price(call):
    bot.answer_callback_query(call.id)
    _, coin_id, fiat = call.data.split("_")
    price = get_price(coin_id, fiat)

    if price:
        symbols = {"usd": "$", "eur": "€", "rub": "₽", "jpy": "¥"}
        sym = symbols.get(fiat, "")

        markup = types.InlineKeyboardMarkup(row_width=2)

        button = types.InlineKeyboardButton(text="🧮 Рассчитать стоимость", callback_data=f"calc_{price}_{sym}")
        button2 = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")

        markup.add(button, button2)

        text = f"📈 Курс {coin_id.capitalize()}: {price} {sym}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif price is None:
        bot.send_message(call.message.chat.id, "⚠️ Ошибка API. Попробуй позже.")
        return

@bot.callback_query_handler(func=lambda call: call.data.startswith("calc_"))
def callback_calc(call):
    markup = types.InlineKeyboardMarkup(row_width=2)

    button_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")

    markup.add(button_back)

    bot.answer_callback_query(call.id)
    _, price, sym = call.data.split("_")
    msg = bot.send_message(call.message.chat.id, f"🪙 Сколько монет у тебя есть? (Результат будет в {sym})\n\nВведи число:")
    bot.register_next_step_handler(msg, calculate, float(price), sym)

def calculate(message, price, sym):
    try:
        amount = float(message.text.replace(',', '.'))
        result = round(price * amount, 2)
        bot.send_message(message.chat.id, f"💰 Твои монеты стоят {result} {sym}.")
        start_handler(message)

    except ValueError:
        bot.send_message(message.chat.id, "❌ Введи числовое значение!")
        start_handler(message)

# блок расходы
@bot.callback_query_handler(func=lambda call: call.data == "add_spendings")
def choose_category(call):
    bot.answer_callback_query(call.id)

    markup = types.InlineKeyboardMarkup(row_width=2)

    for category in CATEGORIES:
        item = types.InlineKeyboardButton(text=category, callback_data=f"cat_{category}")
        markup.add(item)

    button_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")

    markup.add(button_back)

    bot.edit_message_text("💰 Выбери категорию или вернись назад:", message_id=call.message.message_id, chat_id=call.message.chat.id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    bot.answer_callback_query(call.id)
    # Сбрасываем ожидание ввода, если оно было активно
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="🌟 Привет!\n\n💸 Я бот финансист...", reply_markup=main_menu_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def ask_spending_currency(call):
    bot.answer_callback_query(call.id)
    category = call.data.split("_")[1]  
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_usd = types.InlineKeyboardButton("💵 USD", callback_data=f"spend_{category}_usd")
    btn_eur = types.InlineKeyboardButton("💶 EUR", callback_data=f"spend_{category}_eur")
    btn_rub = types.InlineKeyboardButton("💳 RUB", callback_data=f"spend_{category}_rub")
    btn_jpy = types.InlineKeyboardButton("💴 JPY", callback_data=f"spend_{category}_jpy")
    button_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")

    markup.add(btn_usd, btn_eur, btn_rub, btn_jpy, button_back)

    bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id, text=f"В какой валюте была трата на категорию {category}?", reply_markup=markup,)

@bot.callback_query_handler(func=lambda call: call.data.startswith("spend_"))
def callback_spending_currency(call):
    markup = types.InlineKeyboardMarkup()

    button_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")

    markup.add(button_back)

    bot.answer_callback_query(call.id)
    _, category, fiat = call.data.split("_")
    msg = bot.send_message(call.message.chat.id, f"Сколько ты потратил в {fiat.upper()}?")
    # Передаем и категорию, и валюту в финальную функцию записи
    bot.register_next_step_handler(msg, how_much_spend, category, fiat)

def how_much_spend(message, category, fiat):
    try:
        amount = float(message.text.replace(',', '.'))
        filename = f"spendings_{message.chat.id}.txt"
        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"[{now}] {category}: {amount} {fiat.upper()}\n")
        bot.send_message(message.chat.id, f"✅ Записал: {category} — {amount} {fiat.upper()}")
        start_handler(message)

    except ValueError:
        bot.send_message(message.chat.id, "❌ Введи числовое значение!")
        start_handler(message)

@bot.callback_query_handler(func=lambda call: call.data == "read_spendings")
def send_spendings(call):
    markup = types.InlineKeyboardMarkup()

    button_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")

    markup.add(button_back)

    bot.answer_callback_query(call.id)
    filename = f"spendings_{call.message.chat.id}.txt"

    if not os.path.exists(filename):
        bot.send_message(call.message.chat.id, "❌ Список пока пуст!")
        start_handler(call.message)

    with open(filename, "r", encoding="utf-8") as f:
        spendings = f.readlines()

    if not spendings:
        bot.send_message(call.message.chat.id, "❌ Список пока пуст!")
        start_handler(call.message)

    text_report = "📋 Твои траты:\n\n" + "".join(spendings)
    bot.send_message(call.message.chat.id, text_report, reply_markup=markup)

# блок для удаления файла
@bot.callback_query_handler(func=lambda call: call.data == "clear_history")
def confirm_clear(call):
    bot.answer_callback_query(call.id)

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_yes = types.InlineKeyboardButton("✅ Да, очистить", callback_data="clear_yes")
    btn_no = types.InlineKeyboardButton("❌ Нет, оставить", callback_data="clear_no")
    markup.add(btn_yes, btn_no)

    bot.send_message(call.message.chat.id, "❗ Ты уверен, что хочешь удалить все записи?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("clear_"))
def callback_clear(call):
    bot.answer_callback_query(call.id)

    if call.data == "clear_yes":
        filename = f"spendings_{call.message.chat.id}.txt"

        if os.path.exists(filename):
            os.remove(filename)
            bot.edit_message_text("✅ История успешно удалена!", call.message.chat.id, call.message.message_id)
            start_handler(call.message)

        else:
            bot.edit_message_text("❌ Файл и так пуст.", call.message.chat.id, call.message.message_id)
            start_handler(call.message)

    else:
        bot.edit_message_text("🏠 Удаление отменено.", call.message.chat.id, call.message.message_id)
        start_handler(call.message)

# 1. Выбор базовой валюты
@bot.callback_query_handler(func=lambda call: call.data == "check_money")
def exchange_menu(call):
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    # Список валют для обмена
    fiats = {"USD ➡️ RUB": "USD_RUB", "EUR ➡️ RUB": "EUR_RUB", "USD ➡️ EUR": "USD_EUR"}
    
    for name, res in fiats.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"exc_{res}"))
    
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))
    bot.edit_message_text("💱 Что во что переводим?", call.message.chat.id, call.message.message_id, reply_markup=markup)

# 2. Ловим выбор и запрашиваем сумму
@bot.callback_query_handler(func=lambda call: call.data.startswith("exc_"))
def ask_exc_amount(call):
    bot.answer_callback_query(call.id)
    _, pair = call.data.split("_", 1) # Получим например "USD_RUB"
    base, target = pair.split("_")
    
    msg = bot.send_message(call.message.chat.id, f"Введите сумму в {base} для перевода в {target}:")
    bot.register_next_step_handler(msg, perform_exchange, base, target)

# 3. Финальный расчет
def perform_exchange(message, base, target):
    try:
        amount = float(message.text.replace(',', '.'))
        rate = get_fiat_rate(base, target)
        
        if rate:
            res = round(amount * rate, 2)
            bot.send_message(message.chat.id, f"✅ {amount} {base} = {res} {target}\nКурс: {rate}")
        else:
            bot.send_message(message.chat.id, "⚠️ Ошибка API.")
        start_handler(message)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Нужно число!")
        start_handler(message)

print("Bot is running...")
bot.infinity_polling(skip_pending=True)