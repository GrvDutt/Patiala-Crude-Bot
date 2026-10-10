import os, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK v5.3")
 def do_HEAD(self): self.send_response(200); self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get("PORT", 10000))
 HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

import time, pytz, requests, yfinance as yf, telebot
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004448478970"))
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
IST = pytz.timezone('Asia/Kolkata')
pinned_id = None
last_crude_price = 0

def get_inr():
 try: return requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()['rates']['INR']
 except: return 88.0

def get_data(sym):
 try:
  h = yf.Ticker(sym).history(period="2d")
  if h.empty: return None
  c = float(h['Close'].iloc[-1])
  p = float(h['Close'].iloc[-2]) if len(h)>1 else c
  ch = ((c-p)/p*100) if p else 0
  return {"price":c,"high":float(h['High'].iloc[-1]),"low":float(h['Low'].iloc[-1]),"change":ch}
 except: return None

def impact(head):
 hl = head.lower()
 if "cut" in hl or "war" in hl or "tension" in hl: return "🟢 BULLISH"
 if "high" in hl or "surplus" in hl or "recession" in hl: return "🔴 BEARISH"
 return "🔵 NEUTRAL"

def get_news():
 try:
  if not FINNHUB_KEY: return "1. Market stable - NEUTRAL"
  r = requests.get(f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}", timeout=8).json()
  txt = ""
  for i in range(min(3,len(r))):
   h = r[i]['headline'][:65]
   txt += f"{i+1}. {h} {impact(h)}\n"
  return txt
 except: return "1. OPEC awaited - NEUTRAL"

def color_fmt(ch, label):
 if ch > 0.10: return f"🟢 {label} (+{ch:.2f}%)"
 if ch < -0.10: return f"🔴 {label} ({ch:.2f}%)"
 return f"🔵 {label} ({ch:.2f}% Stable)"

def make_hi_text():
 inr = get_inr()
 crude = get_data("CL=F")
 nifty = get_data("^NSEI")
 sensex = get_data("^BSESN")
 sp = get_data("^GSPC")
 nas = get_data("^IXIC")
 gold = get_data("GC=F")
 now = datetime.now(IST).strftime('%I:%M %p, %d %b')
 news = get_news()

 msg = f"📌 <b>PATIALA CRUDE LIVE - {now}</b>\n\n"

 if crude:
  crude_label = f"${crude['price']:.2f} (Rs {crude['price']*inr:,.0f})"
  msg += f"🛢️ <b>CRUDE OIL</b>\n"
  msg += color_fmt(crude['change'], crude_label) + "\n"
  emo = "BULLISH 🟢" if crude['change']>0.5 else "BEARISH 🔴" if crude['change']<-0.5 else "STABLE 🔵"
  msg += f"Emotion: {emo}\n\n"

 if nifty:
  msg += f"🇮🇳 NIFTY: {color_fmt(nifty['change'], str(round(nifty['price'],2)))}\n"
 if sensex:
  msg += f"SENSEX: {color_fmt(sensex['change'], str(round(sensex['price'],2)))}\n"
 if sp:
  msg += f"🇺🇸 S&P: {color_fmt(sp['change'], str(round(sp['price'],2)))}\n"
 if nas:
  msg += f"NASDAQ: {color_fmt(nas['change'], str(round(nas['price'],2)))}\n"
 if gold:
  gold_label = f"${gold['price']:.2f}"
  msg += f"💰 GOLD: {color_fmt(gold['change'], gold_label)}\n"

 msg += f"\n🗞️ <b>NEWS</b>\n{news}\n\n<i>Silent Pin | Alert ON</i>"
 return msg

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hii','hello','status'])
def hi_handler(m): bot.send_message(m.chat.id, make_hi_text())

@bot.message_handler(commands=['liveon','pinon'])
def liveon(m):
 global pinned_id
 msg = bot.send_message(GROUP_ID, make_hi_text())
 pinned_id = msg.message_id
 try: bot.pin_chat_message(GROUP_ID, pinned_id, disable_notification=True)
 except: pass

def updater():
 global pinned_id, last_crude_price
 while True:
  try:
   time.sleep(120)
   crude = get_data("CL=F")
   inr = get_inr()
   if not crude: continue
   if pinned_id:
    try: bot.edit_message_text(make_hi_text(), GROUP_ID, pinned_id)
    except: pass
   if last_crude_price!= 0:
    diff = ((crude['price']-last_crude_price)/last_crude_price*100)
    if abs(diff) >= 0.70:
     tag = "HIGH" if diff>0 else "LOW"
     bot.send_message(GROUP_ID, f"🚨 SUDDEN {tag} {diff:+.2f}% 🛢️ ${crude['price']:.2f}", disable_notification=False)
   last_crude_price = crude['price']
  except Exception as e:
   print(e)
   time.sleep(60)

threading.Thread(target=updater, daemon=True).start()
bot.infinity_polling(none_stop=True, timeout=90)
