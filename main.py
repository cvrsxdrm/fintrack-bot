import requests

import sqlite3

import os

import telebot

from telebot import types

from config import TOKEN

from datetime import datetime

bot = telebot.TeleBot(TOKEN)

CURRENCIES = {"🪙 BTC": "bitcoin", "🔹 ETH": "ethereum", "💲 USDT": "tether"}

CATEGORIES = ["Еда", "Транспорт", "Развлечения"]



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
    markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
    button1 = types.KeyboardButton("💰 Криптовалюты")
    button2 = types.KeyboardButton("💸 Добавить расход")
    button3 = types.KeyboardButton("📋 Посмотреть расходы")
    button4 = types.KeyboardButton("🗑️ Очистить историю")
    markup.add(button1, button2, button3, button4)

    bot.send_message(message.chat.id, "🌟 Привет!\n\n 💸 Я бот финансист, помогу тебе с финансами.", reply_markup = markup)

@bot.message_handler(func=lambda message: message.text == "💰 Криптовалюты")
def choose_currency(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for coin_name in CURRENCIES.keys():
        item = types.KeyboardButton(coin_name)
        markup.add(item)

    button_back = types.KeyboardButton("⬅️ Назад")
    markup.add(button_back)

    bot.send_message(message.chat.id, "📈 Выбери монету или вернись назад:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in CURRENCIES)
def ask_fiat_currency(message):
    coin_id = CURRENCIES[message.text]
    markup = types.InlineKeyboardMarkup()  

    # Кнопки с валютами. В callback_data прячем ID монеты и саму валюту
    btn_usd = types.InlineKeyboardButton("💵 USD", callback_data=f"fiat_{coin_id}_usd")
    btn_eur = types.InlineKeyboardButton("💶 EUR", callback_data=f"fiat_{coin_id}_eur")
    btn_rub = types.InlineKeyboardButton("💳 RUB", callback_data=f"fiat_{coin_id}_rub")
    btn_jpy = types.InlineKeyboardButton("💴 JPY", callback_data=f"fiat_{coin_id}_jpy")

    markup.add(btn_usd, btn_eur, btn_rub, btn_jpy)
    bot.send_message(message.chat.id, f"В какой валюте показать курс {message.text}?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("fiat_"))
def callback_price(call):
    # Разрезаем: fiat_bitcoin_rub -> ['fiat', 'bitcoin', 'rub']
    _, coin_id, fiat = call.data.split("_")
    price = get_price(coin_id, fiat)

    if price:
        symbols = {"usd": "$", "eur": "€", "rub": "₽", "jpy": "¥"}
        sym = symbols.get(fiat, "")
        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(text="🧮 Рассчитать стоимость", callback_data=f"calc_{price}_{sym}")
        markup.add(button)
        text = f"📈 Курс {coin_id.capitalize()}: {price} {sym}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif price is None:
        bot.send_message(call.message.chat.id, "⚠️ Не удалось получить курс. Попробуй позже.")
        return

@bot.callback_query_handler(func=lambda call: call.data.startswith("calc_"))
def callback_calc(call):
    # Теперь тут три части: ['calc', '65000.5', '$']
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
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Отмена"))
        bot.send_message(message.chat.id, "⚠️ Ошибка! Введи только число:", reply_markup=markup)
        bot.register_next_step_handler(message, calculate, price, sym)

@bot.message_handler(func=lambda message: message.text == "💸 Добавить расход")
def choose_category(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for category in CATEGORIES:
        item = types.KeyboardButton(category)
        markup.add(item)

    button_back = types.KeyboardButton("⬅️ Назад")
    markup.add(button_back)

    bot.send_message(message.chat.id, "💰 Выбери категорию или вернись назад:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "⬅️ Назад")
def back_to_main(message):
    start_handler(message)

@bot.message_handler(func=lambda message: message.text in CATEGORIES)
def ask_spending_currency(message):
    category = message.text
    markup = types.InlineKeyboardMarkup()
    # Передаем категорию и валюту через callback
    btn_usd = types.InlineKeyboardButton("💵 USD", callback_data=f"spend_{category}_usd")
    btn_eur = types.InlineKeyboardButton("💶 EUR", callback_data=f"spend_{category}_eur")
    btn_rub = types.InlineKeyboardButton("💳 RUB", callback_data=f"spend_{category}_rub")
    btn_jpy = types.InlineKeyboardButton("💴 JPY", callback_data=f"spend_{category}_jpy")
    markup.add(btn_usd, btn_eur, btn_rub, btn_jpy)

    bot.send_message(message.chat.id, f"В какой валюте была трата на {category}?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("spend_"))
def callback_spending_currency(call):
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
            # ТЕПЕРЬ ЗАПИСЫВАЕМ С ВАЛЮТОЙ!
            f.write(f"[{now}] {category}: {amount} {fiat.upper()}\n")
        bot.send_message(message.chat.id, f"✅ Записал: {category} — {amount} {fiat.upper()}")
        start_handler(message)

    except ValueError:
        bot.send_message(message.chat.id, "⚠️ Ошибка! Введи число:")
        bot.register_next_step_handler(message, how_much_spend, category, fiat)

@bot.message_handler(func=lambda message: message.text == "📋 Посмотреть расходы")
def send_spendings(message):
    filename = f"spendings_{message.chat.id}.txt"

    if not os.path.exists(filename):
        bot.send_message(message.chat.id, "❌ Список пока пуст!")
        return

    with open(filename, "r", encoding="utf-8") as f:
        spendings = f.readlines()

    if not spendings:
        bot.send_message(message.chat.id, "❌ Список пока пуст!")
        return

    text_report = "📋 **Твои траты:**\n\n" + "".join(spendings)
    bot.send_message(message.chat.id, text_report, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🗑️ Очистить историю")
def confirm_clear(message):
    markup = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton("✅ Да, очистить", callback_data="clear_yes")
    btn_no = types.InlineKeyboardButton("❌ Нет, оставить", callback_data="clear_no")
    markup.add(btn_yes, btn_no)

    bot.send_message(message.chat.id, "❗ Ты уверен, что хочешь удалить все записи?", reply_markup=markup)

# Обработчик кнопок удаления
@bot.callback_query_handler(func=lambda call: call.data.startswith("clear_"))
def callback_clear(call):

    if call.data == "clear_yes":
        filename = f"spendings_{call.message.chat.id}.txt"

        if os.path.exists(filename):
            os.remove(filename)
            bot.edit_message_text("✅ История успешно удалена!", call.message.chat.id, call.message.message_id)

        else:
            bot.edit_message_text("❌ Файл и так пуст.", call.message.chat.id, call.message.message_id)

    else:
        bot.edit_message_text("🏠 Удаление отменено.", call.message.chat.id, call.message.message_id)

print("Bot is running...")
bot.infinity_polling(skip_pending=True)