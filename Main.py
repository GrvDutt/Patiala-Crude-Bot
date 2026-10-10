import os, threading, json
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v8.6 GUARANTEED LIVE")
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get("PORT", 10000))
 print("Health server starting on port", port)
 HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

print("Step 1 - Health OK")
import pytz, requests, telebot, feedparser
from datetime import datetime
import time
print("Step 2 - Basic imports OK")

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID", "-1004448478970")
print("Step 3 - Token check:", "FOUND" if BOT_TOKEN else "MISSING - SET IN RENDER ENV!")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN missing in Render Environment!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
try:
    bot.delete_webhook(drop_pending_updates=True)
    print("Step 4 - Webhook deleted, polling mode ON")
except Exception as e:
    print("Webhook delete error:", e)

IST = pytz.timezone('Asia/Kolkata')
pinned_id = None

def get_data_safe(sym):
  try:
    import yfinance as yf
    h = yf.Ticker(sym).history(period='2d')
    if h.empty: return None
    c = float(h['Close'].iloc[-1])
    p = float(h['Close'].iloc[-2]) if len(h)>1 else c
    ch = ((c-p)/p*100) if p else 0
    return {'price':c,'change':ch}
  except Exception as e:
    print("get_data error for", sym, e)
    return None

def get_rss_news(query, limit=1):
  try:
    url = 'https://news.google.com/rss/search?q=' + query + '&hl=en-IN&gl=IN&ceid=IN:en'
    feed = feedparser.parse(url)
    txt = ''
    if feed.entries:
      for i in range(min(limit, len(feed.entries))):
        h = feed.entries[i].title[:70].replace('<','').replace('>','')
        txt += str(i+1) + '. ' + h + '\n'
    return txt
  except Exception as e:
    print("RSS error", e)
    return 'News temporarily unavailable\n'

def make_hi_text():
 try:
  crude = get_data_safe('CL=F')
  nifty = get_data_safe('^NSEI')
  now = datetime.now(IST).strftime('%I:%M %p, %d %b')
  msg = 'PATIALA CRUDE LIVE - ' + now + '\n\n'
  if crude:
    msg += 'CRUDE: $' + str(round(crude['price'],2)) + ' (' + str(round(crude['change'],2)) + '%)\n'
  else:
    msg += 'CRUDE: Fetching... (yfinance slow)\n'
  if nifty:
    msg += 'NIFTY: ' + str(round(nifty['price'],2)) + ' (' + str(round(nifty['change'],2)) + '%)\n'
  msg += '\nCRUDE NEWS\n' + get_rss_news('crude oil OPEC', 2) + '\n'
  msg += 'NIFTY IMPACT\n' + get_rss_news('Nifty Sensex RBI', 1) + '\n'
  msg += 'WORLD LEADERS AND WAR\n' + get_rss_news('US President Putin Israel Iran attack', 2) + '\n'
  msg += 'BIG TRADERS\n' + get_rss_news('NSE Bulk Deal FII', 1) + '\n'
  return msg
 except Exception as e:
  print("make_hi_text error", e)
  return 'Bot LIVE but data error: ' + str(e) + '\nTry again in 30 sec'

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hii','hello','status'])
def hi_handler(m):
 print("HI received from", m.chat.id, m.text)
 try:
  bot.send_message(m.chat.id, make_hi_text())
 except Exception as e:
  print("Send error", e)
  bot.send_message(m.chat.id, "Bot LIVE - data fetching, try hi again in 10 sec")

@bot.message_handler(commands=['liveon','pinon'])
def liveon(m):
 global pinned_id
 msg = bot.send_message(int(GROUP_ID), make_hi_text())
 pinned_id = msg.message_id
 try:
  bot.pin_chat_message(int(GROUP_ID), pinned_id, disable_notification=True)
 except:
  pass

def updater():
 global pinned_id
 while True:
  try:
   time.sleep(900)
   print("15 min update tick")
   if pinned_id:
    try:
     bot.edit_message_text(make_hi_text(), int(GROUP_ID), pinned_id)
    except Exception as e:
     print("Edit error", e)
  except Exception as e:
   print("Updater error", e)
   time.sleep(60)

threading.Thread(target=updater, daemon=True).start()

print("Step 5 - Starting polling...")
while True:
    try:
        print("Bot polling started v8.6 GUARANTEED LIVE")
        bot.infinity_polling(none_stop=True, timeout=90, skip_pending=True)
    except Exception as e:
        print("Polling error", e)
        time.sleep(10)
