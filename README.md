# 💰 FinTrack Bot (WIP)

**FinTrack Bot** is your personal assistant for managing personal finances and monitoring cryptocurrency assets directly within Telegram.

> ⚠️ **Status:** Work In Progress (WIP).

---

## ✨ Key Features

* **📈 Crypto Monitoring:** Fetch real-time exchange rates for BTC, ETH, and USDT (via CoinGecko API).
* **💱 Multi-Currency Support:** View rates and calculate asset values in **USD, EUR, RUB, and JPY**.
* **💸 Expense Tracking:** Log spending by categories (Food, Transport, Entertainment) with currency tags.
* **📊 Transaction History:** View a complete list of your recorded expenses.
* **🧮 Built-in Calculator:** Quickly calculate the value of your crypto holdings based on current market prices.

---

## 🛠 Tech Stack

* **Language:** [Python 3.x](https://www.python.org/)
* **Library:** [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) (Telebot)
* **API:** [CoinGecko API](https://www.coingecko.com/en/api)
* **Data Storage:** Flat files (`.txt`) — *migration to SQLite3 is planned*.
* **Hosting:** [PythonAnywhere](https://www.pythonanywhere.com/)

---

## 🚀 Getting Started (Local Launch)

### How to Run:
1. Clone the repository.
2. Create a `config.py` file in the root directory.
3. Add your bot token: `TOKEN = 'your_token_here'`.
4. Run `python main.py`.
