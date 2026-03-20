import requests
import os
import sqlite3
import telebot
from telebot import types
from config import TOKEN
from datetime import datetime

bot = telebot.TeleBot(TOKEN)

CURRENCIES = {"🪙 BTC": "bitcoin", "🔹 ETH": "ethereum"}
MONEY = {"USD": "tether", "EUR": "eur", "RUB": "rub", "JPY": "jpy"}

CATEGORIES = ["Еда", "Транспорт", "Развлечения"]

def main_menu_markup():

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton("💰 Криптовалюты", callback_data="crypto_menu"),
        types.InlineKeyboardButton("💸 Добавить расход", callback_data="add_spendings"),
        types.InlineKeyboardButton("📋 Посмотреть расходы", callback_data="read_spendings"),
        types.InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history"),
        types.InlineKeyboardButton("💳 Валюты", callback_data="check_money"))
    
    return markup

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

    button_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")

    markup.add(button_back)

    bot.edit_message_text("📈 Выбери монету или вернись назад:", message_id=call.message.message_id, chat_id=call.message.chat.id, reply_markup=markup)

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

        markup.add(button)

        text = f"📈 Курс {coin_id.capitalize()}: {price} {sym}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif price is None:
        bot.send_message(call.message.chat.id, "⚠️ Ошибка API. Попробуй позже.")
        return

@bot.callback_query_handler(func=lambda call: call.data.startswith("calc_"))
def callback_calc(call):
    bot.answer_callback_query(call.id)
    _, price, sym = call.data.split("_")
    msg = bot.send_message(call.message.chat.id, f"🪙 Сколько монет у тебя есть? (Результат будет в {sym})\n\nВведи число:")
    bot.register_next_step_handler(msg, calculate, float(price), sym)

def calculate(message, price, sym):
    if message.text == "❌ Отмена":
        bot.send_message(message.chat.id, "🏠 Возвращаемся в главное меню.", reply_markup=None)
        start_handler(message)
        return

    try:
        amount = float(message.text.replace(',', '.'))
        result = round(price * amount, 2)
        bot.send_message(message.chat.id, f"💰 Твои монеты стоят {result} {sym}.")
        start_handler(message)

    except ValueError:

        markup = types.InlineKeyboardMarkup(row_width=2)

        markup.add(types.InlineKeyboardButton("❌ Отмена"))

        bot.send_message(message.chat.id, "❌ Введи числовое значение!", reply_markup=markup)

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

    markup.add(btn_usd, btn_eur, btn_rub, btn_jpy)

    bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id, text=f"В какой валюте была трата на категорию {category}?", reply_markup=markup,)

@bot.callback_query_handler(func=lambda call: call.data.startswith("spend_"))
def callback_spending_currency(call):
    bot.answer_callback_query(call.id)
    _, category, fiat = call.data.split("_")
    msg = bot.send_message(call.message.chat.id, f"Сколько ты потратил в {fiat.upper()}?")
    # Передаем и категорию, и валюту в финальную функцию записи
    bot.register_next_step_handler(msg, how_much_spend, category, fiat)

def how_much_spend(message, category, fiat):
    if message.text == "❌ Отмена":
        bot.send_message(message.chat.id, "🏠 Возвращаемся в главное меню.")
        start_handler(message)
        return

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
        bot.register_next_step_handler(message, how_much_spend, category, fiat)

@bot.callback_query_handler(func=lambda call: call.data == "read_spendings")
def send_spendings(call):
    bot.answer_callback_query(call.id)
    filename = f"spendings_{call.message.chat.id}.txt"

    if not os.path.exists(filename):
        bot.send_message(call.message.chat.id, "❌ Список пока пуст!")
        return

    with open(filename, "r", encoding="utf-8") as f:
        spendings = f.readlines()

    if not spendings:
        bot.send_message(call.message.chat.id, "❌ Список пока пуст!")
        return

    text_report = "📋 Твои траты:\n\n" + "".join(spendings)
    bot.send_message(call.message.chat.id, text_report)

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

        else:
            bot.edit_message_text("❌ Файл и так пуст.", call.message.chat.id, call.message.message_id)

    else:
        bot.edit_message_text("🏠 Удаление отменено.", call.message.chat.id, call.message.message_id)

# 1. Выбор валюты
@bot.callback_query_handler(func=lambda call: call.data == "check_money")
def choose_money(call):
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    for name, code in MONEY.items():
        btn = types.InlineKeyboardButton(name, callback_data=f"fiatconv_{code}")
        markup.add(btn)

    bot.edit_message_text("📈 Выбери валюту, которую хочешь купить за USD:", call.message.chat.id, call.message.message_id, reply_markup=markup)

# 2. Ловим выбор и спрашиваем сумму
@bot.callback_query_handler(func=lambda call: call.data.startswith("fiatconv_"))
def ask_amount_fiat(call):
    bot.answer_callback_query(call.id)
    target_fiat = call.data.split("_")[1]
    msg = bot.send_message(call.message.chat.id, f"Введите сумму в USD для перевода в {target_fiat.upper()}:")
    # Передаем выбранную валюту дальше в функцию расчета
    bot.register_next_step_handler(msg, calculate_fiat, target_fiat)

# 3. Сама функция расчета
def calculate_fiat(message, target_fiat):
    try:
        usd_amount = float(message.text.replace(',', '.'))
        # Используем твою функцию get_price.
        # Т.к. CoinGecko — крипто-сервис, берем tether как эквивалент USD
        rate = get_price("tether", target_fiat)

        if rate:
            result = round(usd_amount * rate, 2)
            bot.send_message(message.chat.id, f"✅ {usd_amount} USD = {result} {target_fiat.upper()}\n(Курс: {rate})")
        else:
            bot.send_message(message.chat.id, "⚠️ Ошибка API. Попробуй позже.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введи числовое значение!")

print("Bot is running...")
bot.infinity_polling(skip_pending=True)
