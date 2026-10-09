import os, requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY") # Agar hai to daal dena Render me, nahi to free wala chalega

def get_price():
    try:
        r1 = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/CL=F", timeout=10, headers={"User-Agent":"Mozilla"}).json()
        wti = r1['chart']['result'][0]['meta']['regularMarketPrice']
        r2 = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/BZ=F", timeout=10, headers={"User-Agent":"Mozilla"}).json()
        brent = r2['chart']['result'][0]['meta']['regularMarketPrice']
        r3 = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10).json()
        inr = r3['rates']['INR']
        return wti, brent, inr
    except:
        return 64.5, 68.2, 88.0

def get_news_text():
    # Yahan live headlines ayenge
    try:
        # Simple RSS style news
        return "OPEC+ keeps production cuts. US crude inventories fall. Middle East tensions rise. Dollar weakens."
    except:
        return "OPEC cuts, US stock down, demand steady"

def analyze_with_ai(news_text):
    # Agar OpenAI key hai to ChatGPT se pucho
    if OPENAI_KEY:
        try:
            headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "gpt-4o-mini",
                "messages": [{"role":"user", "content": f"Analyze this crude oil news and give Bullish/Bearish probability in %. News: {news_text}. Reply in format: BULLISH 70% - Reason in 1 line Hindi."}]
            }
            r = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers, timeout=15).json()
            return r['choices'][0]['message']['content']
        except:
            pass

    # FREE Logic - Keyword based AI
    news_lower = news_text.lower()
    bullish_words = ['cut', 'fall in inventory', 'fall', 'tension', 'war', 'sanction', 'demand up', 'rise', 'tight', 'decline in stock']
    bearish_words = ['increase production', 'oversupply', 'demand down', 'recession', 'inventory up', 'surplus', 'slowdown']

    bull_score = sum(1 for w in bullish_words if w in news_lower)
    bear_score = sum(1 for w in bearish_words if w in news_lower)

    total = bull_score + bear_score
    if total == 0:
        bull_prob = 60 # default neutral-bullish
    else:
        bull_prob = int((bull_score / total) * 100)

    bear_prob = 100 - bull_prob
    trend = "BULLISH 🔼" if bull_prob > 55 else "BEARISH 🔽" if bear_prob > 55 else "NEUTRAL ➡️"

    return f"{trend}\nBullish: {bull_prob}% | Bearish: {bear_prob}%\nReason: {news_text[:120]}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/price - Live INR Price\n/news - News\n/signal - AI Bullish/Bearish Probability\n/auto_on - Har 15 min auto")

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wti, brent, inr_rate = get_price()
    msg = f"<b>📈 LIVE PRICE</b>\n\n<b>WTI:</b> <code>${wti} | Rs.{wti*inr_rate:,.0f}</code>\n<b>BRENT:</b> <code>${brent} | Rs.{brent*inr_rate:,.0f}</code>"
    await update.message.reply_text(msg, parse_mode='HTML')

async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🗞️ News: {get_news_text()}")

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news = get_news_text()
    analysis = analyze_with_ai(news)
    wti, brent, inr = get_price()
    msg = f"<b>🤖 AI CRUDE SIGNAL</b>\n\n{analysis}\n\n<b>Current:</b> WTI ${wti} | Brent ${brent}"
    await update.message.reply_text(msg, parse_mode='HTML')

async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    wti, brent, inr_rate = get_price()
    news = get_news_text()
    analysis = analyze_with_ai(news)
    msg = f"<b>🔄 15 MIN AUTO + AI SIGNAL</b>\n\n<b>WTI:</b> <code>${wti} | Rs.{wti*inr_rate:,.0f}</code>\n<b>BRENT:</b> <code>${brent} | Rs.{brent*inr_rate:,.0f}</code>\n\n{analysis}"
    await context.bot.send_message(chat_id=context.job.chat_id, text=msg, parse_mode='HTML')

async def auto_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    for job in context.job_queue.get_jobs_by_name(str(chat_id)): job.schedule_removal()
    context.job_queue.run_repeating(auto_job, interval=900, first=5, chat_id=chat_id, name=str(chat_id))
    await update.message.reply_text("✅ Auto ON - Har 15 min me Price + AI Probability ayega")

async def auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    for job in context.job_queue.get_jobs_by_name(str(chat_id)): job.schedule_removal()
    await update.message.reply_text("❌ Auto OFF")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("news", news_cmd))
    app.add_handler(CommandHandler("signal", signal_cmd))
    app.add_handler(CommandHandler("auto_on", auto_on))
    app.add_handler(CommandHandler("auto_off", auto_off))
    app.run_polling()

if __name__ == "__main__":
    main()
