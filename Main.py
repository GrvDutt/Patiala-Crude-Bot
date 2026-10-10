import os, threading, json, time, requests, feedparser, pytz, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v8.8 FAST FIXED LIVE")
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get("PORT", 10000))
 print("Health server on port", port)
 HTTPServer(('0.0.0.0', port), H).serve_forever()

threading.Thread(target=run_health, daemon=True).start()
print("Step 1 - Health OK")

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID", "-1004448478970")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN missing!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
try:
    bot.delete_webhook(drop_pending_updates=True)
    print("Step 2 - Webhook deleted")
except Exception as e:
    print("Webhook error", e)

IST = pytz.timezone('Asia/Kolkata')
pinned_id = None
CACHE = {"news": {}, "time": 0}

def get_data_safe(sym):
    try:
        import yfinance as yf
        h = yf.Ticker(sym).history(period='2d')
        if h.empty:
            return None
        c = float(h['Close'].iloc[-1])
        p = float(h['Close'].iloc[-2]) if len(h) > 1 else c
        ch = ((c - p) / p * 100) if p else 0
        return {'price': c, 'change': ch}
    except Exception as e:
        print("get_data error", sym, e)
        return None

def fetch_news_fast(query):
    try:
        url = "https://news.google.com/rss/search?q=" + query + "&hl=en-IN&gl=IN&ceid=IN:en"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=8)
        feed = feedparser.parse(r.content)
        txt = ""
        if feed.entries:
            for i in range(min(2, len(feed.entries))):
                h = feed.entries[i].title[:85].replace('<','').replace('>','')
                txt += str(i+1) + ". " + h + "\n"
            return txt
    except Exception as e:
        print("News error", query, e)
    return "Market stable - No major breaking\n"

def refresh_cache():
    print("Refreshing cache...")
    try:
        CACHE["news"]["crude"] = fetch_news_fast('crude+oil+OPEC+inventory')
        CACHE["news"]["nifty"] = fetch_news_fast('Nifty+Sensex+RBI+FII+DII')
        CACHE["news"]["world"] = fetch_news_fast('US+President+Putin+Xi+Israel+Iran+attack+war')
        CACHE["news"]["bulk"] = fetch_news_fast('NSE+Bulk+Deal+Block+Deal+FII+buying')
        CACHE["time"] = time.time()
        print("Cache OK")
    except Exception as e:
        print("Cache error", e)

threading.Thread(target=refresh_cache, daemon=True).start()

def make_hi_text():
    try:
        if time.time() - CACHE["time"] > 900:
            threading.Thread(target=refresh_cache, daemon=True).start()
        crude = get_data_safe('CL=F')
        nifty = get_data_safe('^NSEI')
        sensex = get_data_safe('^BSESN')
        vix = get_data_safe('^INDIAVIX')
        usdinr = get_data_safe('INR=X')
        now = datetime.now(IST).strftime('%I:%M %p, %d %b')
        msg = "<b>PATIALA CRUDE LIVE - " + now + "</b>\n\n"
        if crude:
            msg += "CRUDE: $" + str(round(crude['price'],2)) + " (" + str(round(crude['change'],2)) + "%)\n"
        if nifty:
            msg += "NIFTY: " + str(round(nifty['price'],2)) + " (" + str(round(nifty['change'],2)) + "%)\n"
        if sensex:
            msg += "SENSEX: " + str(round(sensex['price'],2)) + "\n"
        if vix:
            msg += "VIX: " + str(round(vix['price'],2)) + "\n"
        if usdinr:
            msg += "USD INR: " + str(round(usdinr['price'],2)) + "\n"
        msg += "\n<b>CRUDE IMPACT</b>\n" + CACHE["news"].get("crude","Loading...\n") + "\n"
        msg += "<b>NIFTY SENSEX IMPACT</b>\n" + CACHE["news"].get("nifty","Loading...\n") + "\n"
        msg += "<b>WORLD LEADERS + WAR ALERT</b>\n" + CACHE["news"].get("world","Loading...\n") + "\n"
        msg += "<b>BIG TRADERS BULK</b>\n" + CACHE["news"].get("bulk","Loading...\n") + "\n"
        return msg
    except Exception as e:
        print("make_hi error", e)
        return "Bot LIVE - Loading... " + str(e)

def get_nifty_plan_text():
    try:
        nifty_data = get_data_safe('^NSEI')
        if nifty_data:
            base = int(nifty_data['price'] / 50) * 50
            res1 = base + 80
            res2 = base + 150
            sup1 = base - 100
            sup2 = base - 200
        else:
            res1 = 22580
            res2 = 22600
            sup1 = 22400
            sup2 = 22220
        msg = "<b>NIFTY PLAN - WORLD IMPACT</b>\n"
        msg += "FAST READ LONG: " + str(res1) + " upar = LONG " + str(res2) + "\n"
        msg += "SHORT: " + str(sup2) + " tode = SHORT\n"
        msg += "Res: " + str(res1) + " -> " + str(res2) + "\n"
        msg += "Sup: " + str(sup1) + " -> " + str(sup2) + "\n"
        return msg
    except Exception as e:
        return "Plan loading... " + str(e)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hii','hello','status','hey'])
def hi_handler(m):
    print("HI from", m.chat.id)
    bot.send_message(m.chat.id, make_hi_text())

@bot.message_handler(func=lambda m: m.text and 'plan' in m.text.lower() and not m.text.startswith('/'))
def plan_handler(m):
    bot.send_message(m.chat.id, get_nifty_plan_text())

@bot.message_handler(commands=['liveon','pinon'])
def liveon(m):
    global pinned_id
    try:
        msg = bot.send_message(int(GROUP_ID), make_hi_text())
        pinned_id = msg.message_id
        try:
            bot.pin_chat_message(int(GROUP_ID), pinned_id, disable_notification=True)
        except:
            pass
        bot.reply_to(m, "Live started")
    except Exception as e:
        bot.reply_to(m, "Error: " + str(e))

def updater():
    global pinned_id
    while True:
        try:
            time.sleep(900)
            print("15 min tick")
            if pinned_id:
                try:
                    bot.edit_message_text(make_hi_text(), int(GROUP_ID), pinned_id)
                except:
                    pass
            refresh_cache()
        except:
            time.sleep(60)

threading.Thread(target=updater, daemon=True).start()
print("Step 3 - Starting polling...")
while True:
    try:
        print("Bot polling started v8.8 FAST FIXED LIVE")
        bot.infinity_polling(none_stop=True, timeout=90, skip_pending=True)
    except Exception as e:
        print("Polling error", e)
        time.sleep(10)
