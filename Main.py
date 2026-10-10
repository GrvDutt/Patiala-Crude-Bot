import os, threading, json, time, requests, feedparser, pytz, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# --- 1. HEALTH SERVER FOR RENDER ---
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v8.7 FAST CACHE LIVE")
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get("PORT", 10000))
 print(f"Health server starting on port {port}")
 HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()
print("Step 1 - Health OK")

# --- 2. BOT SETUP ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID", "-1004448478970")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN missing in Render ENV!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
try:
    bot.delete_webhook(drop_pending_updates=True)
    print("Step 2 - Webhook deleted, polling mode ON")
except Exception as e:
    print("Webhook delete error:", e)

IST = pytz.timezone('Asia/Kolkata')
pinned_id = None

# --- 3. FAST CACHE SYSTEM (FIX FOR LATE REPLY) ---
CACHE = {"news": {}, "time": 0}

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
    print(f"get_data error for {sym}: {e}")
    return None

def fetch_news_fast(query):
  try:
    url = f'https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'}
    r = requests.get(url, headers=headers, timeout=8)
    feed = feedparser.parse(r.content)
    txt = ""
    if feed.entries:
      for i in range(min(2, len(feed.entries))):
        h = feed.entries[i].title[:85].replace('<','').replace('>','').replace('"','').replace("'","")
        txt += f"{i+1}. {h}\n"
      return txt
  except Exception as e:
