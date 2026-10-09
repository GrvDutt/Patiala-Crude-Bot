import os
import requests
from flask import Flask
from threading import Thread
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Patiala Crude Bot is Running!"

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "Patiala Crude Bot Ready! /price likho")

@bot.message_handler(commands=['price'])
def price(msg):
    try:
        # Crude Oil Price (WTI)
        r = requests.get("https://api.oilpriceapi.com/v1/prices/latest", timeout=10)
        # Simple fallback
        bot.reply_to(msg, "Current Crude: ~$80-82 (Live API connect karo)")
    except:
        bot.reply_to(msg, "Price fetch error, try again!")

def run_bot():
    bot.infinity_polling()

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    Thread(target=run_bot).start()
    run_web()
