import os, time, threading, pytz
import yfinance as yf
import telebot
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- Render ko zinda rakhne ke liye ---
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200); self.end_headers(); self.wfile.write(b"Live")
 def log_message(self, *a): pass
def run_server():
 HTTPServer(('0.0.0.0', int(os.environ.get("PORT",10000))), H).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004448478970"))
ALERT_PERCENT = 0.5
# ---------------------------------

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
IST = pytz.timezone('Asia/Kolkata')
last_prices = {}

def get_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        if hist.empty: return None
        curr = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2] if len(hist) > 1 else curr
        return {"price": curr, "prev": prev, "high": hist['High'].iloc[-1], "low": hist['Low'].iloc[-1], "avg": hist['Close'].mean(), "change": ((curr - prev)/prev)*100}
    except: return None

HELP_TEXT = """
<b>📜 AVAILABLE COMMANDS</b>
<b>/status</b> - Crude Oil Live
<b>/ind</b> - 🇮🇳 Nifty, Sensex, BankNifty Trend
<b>/us</b> - 🇺🇸 USA Stocks Live
<b>/sum</b> - 🌍 All Global Markets Summary
<b>/all</b> - 💥 Sab kuch ek baar me (Full Report)
<b>?</b> ya <b>/?</b> - Ye help list
"""

@bot.message_handler(commands=['start', 'help', 'commands'])
@bot.message_handler(func=lambda m: m.text and m.text.strip() in ['?', '/?'])
def help_cmd(message): bot.reply_to(message, HELP_TEXT)

@bot.message_handler(commands=['status'])
def status_cmd(message):
    d = get_data("CL=F")
    if not d: return
    trend = "🟢 UP" if d['change'] > 0 else "🔴 DOWN"
    bot.reply_to(message, f"<b>🛢️ CRUDE STATUS</b>\n\nPrice: <b>${d['price']:.2f}</b> ({d['change']:.2f}%) {trend}\nHigh: ${d['high']:.2f} | Low: ${d['low']:.2f}\nAvg: ${d['avg']:.2f}")

@bot.message_handler(commands=['ind'])
def ind_cmd(message):
    nifty = get_data("^NSEI"); sensex = get_data("^BSESN"); bank = get_data("^NSEBANK")
    msg = f"<b>🇮🇳 INDIAN MARKET TREND</b>\n\n"
    if nifty: msg += f"NIFTY: <b>{nifty['price']:.2f}</b> ({nifty['change']:.2f}%) {'🟢' if nifty['change']>0 else '🔴'}\n"
    if sensex: msg += f"SENSEX: <b>{sensex['price']:.2f}</b> ({sensex['change']:.2f}%) {'🟢' if sensex['change']>0 else '🔴'}\n"
    if bank: msg += f"BANKNIFTY: <b>{bank['price']:.2f}</b> ({bank['change']:.2f}%) {'🟢' if bank['change']>0 else '🔴'}\n"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['us'])
def us_cmd(message):
    sp = get_data("^GSPC"); nas = get_data("^IXIC"); dow = get_data("^DJI")
    msg = f"<b>🇺🇸 USA MARKET STATUS</b>\n\n"
    if sp: msg += f"S&P 500: <b>{sp['price']:.2f}</b> ({sp['change']:.2f}%)\n"
    if nas: msg += f"NASDAQ: <b>{nas['price']:.2f}</b>\n"
    if dow: msg += f"DOW: <b>{dow['price']:.2f}</b>\n"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['sum', 'all'])
def all_cmd(message):
    crude = get_data("CL=F"); gold = get_data("GC=F"); nifty = get_data("^NSEI"); sp = get_data("^GSPC")
    msg = f"<b>🌍 ALL MARKET SUMMARY - {datetime.now(IST).strftime('%d %b %I:%M %p')}</b>\n\n"
    if nifty: msg += f"🇮🇳 NIFTY: {nifty['price']:.2f} ({nifty['change']:.2f}%)\n"
    if sp: msg += f"🇺🇸 S&P500: {sp['price']:.2f} ({sp['change']:.2f}%)\n"
    if crude: msg += f"🛢️ CRUDE: ${crude['price']:.2f} ({crude['change']:.2f}%)\n"
    if gold: msg += f"🥇 GOLD: ${gold['price']:.2f} ({gold['change']:.2f}%)\n"
    bot.reply_to(message, msg)

def send_auto(text):
    try: bot.send_message(GROUP_ID, text)
    except Exception as e: print(f"Auto error: {e}")

def scheduled_checker():
    sent_today = set()
    while True:
        try:
            now = datetime.now(IST); curr_time = now.strftime("%H:%M"); today = now.strftime("%Y-%m-%d")
            if curr_time == "09:20" and f"{today}_ind_open" not in sent_today:
                nifty = get_data("^NSEI")
                if nifty: send_auto(f"<b>🇮🇳 MARKET OPEN - 9:20 AM</b>\nNIFTY: <b>{nifty['price']:.2f}</b> ({nifty['change']:.2f}%)")
                sent_today.add(f"{today}_ind_open")
            if curr_time == "13:35" and f"{today}_eu_open" not in sent_today:
                dax = get_data("^GDAXI")
                if dax: send_auto(f"<b>🇪🇺 EUROPE OPEN - 1:35 PM</b>\nDAX: <b>{dax['price']:.2f}</b>")
                sent_today.add(f"{today}_eu_open")
            if curr_time == "19:05" and f"{today}_us_open1" not in sent_today:
                sp = get_data("^GSPC")
                if sp: send_auto(f"<b>🇺🇸 US OPEN - First 30 Min</b>\nS&P500: <b>{sp['price']:.2f}</b>")
                sent_today.add(f"{today}_us_open1")
            if curr_time == "15:40" and f"{today}_ind_close" not in sent_today:
                nifty = get_data("^NSEI")
                if nifty: send_auto(f"<b>🇮🇳 MARKET CLOSE</b>\nClose: <b>{nifty['price']:.2f}</b>")
                sent_today.add(f"{today}_ind_close")
            if curr_time == "01:30" and f"{today}_us_close" not in sent_today:
                sp = get_data("^GSPC")
                if sp: send_auto(f"<b>🇺🇸 US CLOSE</b>\nClose: <b>{sp['price']:.2f}</b>")
                sent_today.add(f"{today}_us_close")
            time.sleep(30)
        except: time.sleep(60)

def sudden_alert_checker():
    while True:
        try:
            for sym, name in [("CL=F", "CRUDE"), ("^NSEI", "NIFTY")]:
                d = get_data(sym)
                if not d: continue
                last = last_prices.get(sym)
                if last:
                    diff = abs((d['price'] - last)/last*100)
                    if diff >= ALERT_PERCENT:
                        send_auto(f"🚨 <b>ALERT - {name} {diff:.2f}%</b>\nPrice: <b>{d['price']:.2f}</b>")
                last_prices[sym] = d['price']
            time.sleep(60)
        except: time.sleep(60)

threading.Thread(target=scheduled_checker, daemon=True).start()
threading.Thread(target=sudden_alert_checker, daemon=True).start()

while True:
    try:
        print("Bot v2.1 Polling ON...")
        bot.infinity_polling(none_stop=True, timeout=90, long_polling_timeout=90)
    except Exception as e:
        print(f"Crash restart in 10s: {e}")
        time.sleep(10)
