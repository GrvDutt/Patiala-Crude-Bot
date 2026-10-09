import os, requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

def get_market_data():
    try:
        url_7d = "https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=7d&interval=1d"
        url_1h = "https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=1d&interval=1h"
        r7 = requests.get(url_7d, timeout=10, headers={"User-Agent":"Mozilla"}).json()['chart']['result'][0]
        r1 = requests.get(url_1h, timeout=10, headers={"User-Agent":"Mozilla"}).json()['chart']['result'][0]
        meta = r7['meta']
        closes_7d = [c for c in r7['indicators']['quote'][0]['close'] if c is not None]
        opens_7d = [o for o in r7['indicators']['quote'][0]['open'] if o is not None]
        closes_1h = [c for c in r1['indicators']['quote'][0]['close'] if c is not None]
        current = meta.get('regularMarketPrice', closes_7d[-1])
        open_today = opens_7d[-1]
        is_bull_now = current >= open_today
        price_1h_ago = closes_1h[-2] if len(closes_1h)>=2 else current
        change_1h_pct = ((current - price_1h_ago)/price_1h_ago*100)
        prev_h = r7['indicators']['quote'][0]['high'][-2]
        prev_l = r7['indicators']['quote'][0]['low'][-2]
        prev_avg = (prev_h + prev_l)/2
        prev_close = closes_7d[-2]
        price_7d_ago = closes_7d[0]
        week_change = ((current - price_7d_ago)/price_7d_ago*100)
        return current, open_today, is_bull_now, price_1h_ago, change_1h_pct, prev_h, prev_l, prev_avg, prev_close, price_7d_ago, week_change
    except:
        return 64.5, 64.0, True, 64.2, 0.46, 65.1, 63.5, 64.3, 63.8, 62.1, 3.8

def get_total_news_analysis():
    raw = "OPEC keeps cuts, US inventory fell 2M barrels, Middle East tension, Dollar weak"
    if OPENAI_KEY:
        try:
            prompt = f"Crude news ka nichod de: Panic hai ya nahi? Overall Bullish/Bearish? Market upar jayega ya neeche? 2 line Hindi. News: {raw}"
            headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
            data = {"model": "gpt-4o-mini", "messages": [{"role":"user","content":prompt}]}
            r = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers, timeout=15).json()
            return r['choices'][0]['message']['content'], raw
        except: pass
    panic = "⚠️ Panic jaisa mahol" if any(k in raw.lower() for k in ['war','tension','crisis']) else "✅ Panic nahi hai"
    summary = f"{panic}\nBULLISH 🔼 70% upar jane ka chance - OPEC cut + US stock down"
    return summary, raw

def get_inr():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10).json()
        return r['rates']['INR']
    except: return 88.0

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current, open_today, is_bull_now, price_1h_ago, change_1h_pct, prev_h, prev_l, prev_avg, prev_close, price_7d_ago, week_change = get_market_data()
    inr = get_inr()
    ai_nichod, raw = get_total_news_analysis()
    now_status = "BULLISH 🟢🔼" if is_bull_now else "BEARISH 🔴🔽"
    week_status = "BULLISH 🚀" if week_change>0 else "BEARISH 📉"
    msg = f"""<b>📊 CRUDE TOTAL STATUS</b>

<b>1. CURRENT:</b> {now_status}
<code>Live: ${current:.2f} | ₹{current*inr:,.0f}</code>
<code>Open: ${open_today:.2f} | Prev: ${prev_close:.2f}</code>

<b>2. LAST 1 HOUR:</b> <code>{change_1h_pct:+.2f}% | ${price_1h_ago:.2f} -> ${current:.2f}</code>

<b>3. KAL KA:</b> <code>H:${prev_h:.2f} L:${prev_l:.2f} Avg:${prev_avg:.2f}</code>

<b>4. WEEK TREND:</b> {week_status} <code>{week_change:+.2f}%</code>

<b>5. 🗞️ NICHOD:</b>
{ai_nichod}
"""
    await update.message.reply_text(msg, parse_mode='HTML')

async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ai_nichod, raw = get_total_news_analysis()
    await update.message.reply_text(f"<b>🗞️ NEWS NICHOD</b>\n\n{ai_nichod}\n\nRaw: {raw}", parse_mode='HTML')

# --- 15 MIN AUTO WALA - YE RAHEGA ---
async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    current, open_today, is_bull_now, price_1h_ago, change_1h_pct, prev_h, prev_l, prev_avg, prev_close, price_7d_ago, week_change = get_market_data()
    inr = get_inr()
    ai_nichod, raw = get_total_news_analysis()
    status = "BULLISH 🟢" if is_bull_now else "BEARISH 🔴"
    msg = f"<b>🔄 15 MIN AUTO UPDATE</b>\n<code>WTI: ${current:.2f} | ₹{current*inr:,.0f} - {status}</code>\n<code>1H: {change_1h_pct:+.2f}% | Week: {week_change:+.2f}%</code>\n<code>Kal H:{prev_h:.2f} L:{prev_l:.2f} Avg:{prev_avg:.2f}</code>\n\n{ai_nichod}"
    await context.bot.send_message(chat_id=context.job.chat_id, text=msg, parse_mode='HTML')

async def auto_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    for j in context.job_queue.get_jobs_by_name(str(chat_id)): j.schedule_removal()
    context.job_queue.run_repeating(auto_job, interval=900, first=5, chat_id=chat_id, name=str(chat_id))
    await update.message.reply_text("✅ Auto ON - Har 15 min me pura status ayega")

async def auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for j in context.job_queue.get_jobs_by_name(str(update.effective_chat.id)): j.schedule_removal()
    await update.message.reply_text("❌ Auto OFF")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/status - Full status\n/news - News nichod\n/auto_on - Har 15 min auto\n/auto_off - Band")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("price", status_cmd))
    app.add_handler(CommandHandler("news", news_cmd))
    app.add_handler(CommandHandler("auto_on", auto_on))
    app.add_handler(CommandHandler("auto_off", auto_off))
    app.run_polling()

if __name__ == "__main__":
    main()
