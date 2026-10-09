import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Patiala Crude Bot Ready! /price likho")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Live WTI Crude Price from Yahoo Finance (No API Key needed)
        url = "https://query1.finance.yahoo.com/v8/finance/chart/CL=F"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        price_val = data['chart']['result'][0]['meta']['regularMarketPrice']
        
        msg = f"🛢️ **Live Crude Oil (WTI)**\n\nCurrent Price: **${price_val}**\n\nPatiala Rate = WTI + Local Charge (aap yahan apna formula laga sakte ho)"
        await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Live price lane me error: {e}\n\nBackup: ~$80-82")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("price", price))

print("Bot Started...")
app.run_polling()
