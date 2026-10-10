import os, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. HEALTH CHECK - Sabse pehle start hoga, Render isi se Live karta hai
class H(BaseHTTPRequestHandler):
 def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
 def do_HEAD(self): self.send_response(200); self.end_headers()
 def log_message(self, *a): pass
def run_health():
 port = int(os.environ.get("PORT", 10000))
 HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

# 2. BAAD ME BOT CODE
import time, pytz, requests
import yfinance as yf
import telebot
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004448478970"))
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
IST = pytz.timezone('Asia/Kolkata')
pinned_id, last_crude_price = None, 0

def get_inr():
 try: return requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()['rates']['INR']
 except: return 88.0
def get_data(s):
 try:
  h=yf.Ticker(s).history(period="2d")
  if h.empty: return None
  c=float(h['Close'].iloc[-1]); p=float(h['Close'].iloc[-2]) if len(h)>1 else c
  return {"price":c,"high":float(h['High'].iloc[-1]),"low":float(h['Low'].iloc[-1]),"change":((c-p)/p*100) if p else 0}
 except: return None
def analyze_impact(head):
 hl=head.lower()
 if any(x in hl for x in ["cut","war","tension","attack","low inventory","sanction"]): return "🟢 BULLISH"
 if any(x in hl for x in ["high inventory","demand down","surplus","recession","strong dollar"]): return "🔴 BEARISH"
 return "🔵 NEUTRAL"
def get_news():
 try:
  if not FINNHUB_KEY: return "1. Market stable - 🔵 NEUTRAL"
  r=requests.get(f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}", timeout=8).json()
  t=""
  for i,n in enumerate(r[:3]): t+=f"{i+1}. {n['headline'][:70]} {analyze_impact(n['headline'])}\n"
  return t
 except: return "1. OPEC update awaited - 🔵 NEUTRAL"
def color_fmt(ch, label):
 if ch>0.10: return f"🟢 {label} (+{ch:.2f}%)"
 elif ch<-0.10: return f"🔴 {label} ({ch:.2f}%)"
 else: return f"🔵 {label} ({ch:.2f}% Stable)"
def make_hi_text():
 inr=get_inr(); crude=get_data("CL=F"); nifty=get_data("^NSEI"); sensex=get_data("^BSESN")
 sp=get_data("^GSPC"); nas=get_data("^IXIC"); gold=get_data("GC=F")
 now=datetime.now(IST).strftime('%I:%M:%S %p, %d %b')
 news=get_news()
 t=f"📌 <b>PATIALA CRUDE LIVE - {now}</b>\n\n"
 if crude:
  t+=f"🛢️ <b>CRUDE OIL:</b> {color_fmt(crude['change'], f\"${crude['price']:.2f} (Rs {crude['price']*inr:,.0f})\")}\n"
  emo="BULLISH 🟢" if crude['change']>0.5 else "BEARISH 🔴" if crude['change']<-0.5 else "STABLE 🔵"
  t+=f"Emotion: {emo}\n\n"
 if nifty: t+=f"🇮🇳 NIFTY: {color_fmt(nifty['change'], str(round(nifty['price'],2)))}\n"
 if sensex: t+=f"SENSEX: {color_fmt(sensex['change'], str(round(sensex['price'],2)))}\n"
 if sp: t+=f"🇺🇸 S&P: {color_fmt(sp['change'], str(round(sp['price'],2)))}\n"
 if nas: t+=f"NASDAQ: {color_fmt(nas['change'], str(round(nas['price'],2)))}\n"
 if gold: t+=f"💰 GOLD: {color_fmt(gold['change'], f\"${gold['price']:.2f}\")}\n"
 t+=f"\n🗞️ <b>NEWS</b>\n{news}\n\n<i>🔕 Silent Pin | 🚨 Alert ON</i>"
 return t

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hii','hello','status'])
def hi_handler(m): bot.send_message(m.chat.id, make_hi_text())
@bot.message_handler(commands=['liveon','pinon'])
def liveon(m):
 global pinned_id
 msg=bot.send_message(GROUP_ID, make_hi_text())
 pinned_id=msg.message_id
 try: bot.pin_chat_message(GROUP_ID, pinned_id, disable_notification=True)
 except: pass

def updater():
 global pinned_id, last_crude_price
 while True:
  try:
   time.sleep(120)
   crude=get_data("CL=F"); inr=get_inr()
   if not crude: continue
   if pinned_id:
    try: bot.edit_message_text(make_hi_text(), GROUP_ID, pinned_id)
    except: pass
   if last_crude_price!=0:
    diff=((crude['price']-last_crude_price)/last_crude_price*100)
    if abs(diff)>=0.70:
     bot.send_message(GROUP_ID, f"🚨 SUDDEN {'HIGH' if diff>0 else 'LOW'} {diff:+.2f}% 🛢️ ${crude['price']:.2f}", disable_notification=False)
   last_crude_price=crude['price']
  except: time.sleep(60)

threading.Thread(target=updater, daemon=True).start()
bot.infinity_polling(none_stop=True, timeout=90)
