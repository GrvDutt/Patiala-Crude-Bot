import os, time, threading, pytz, requests
import yfinance as yf
import telebot
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200); self.end_headers(); self.wfile.write(b"v5.1 Live")
 def log_message(self, *a): pass

def run_server():
 try: HTTPServer(('0.0.0.0', int(os.environ.get("PORT",10000))), H).serve_forever()
 except: pass
threading.Thread(target=run_server, daemon=True).start()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004448478970"))
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
IST = pytz.timezone('Asia/Kolkata')

pinned_id = None
last_crude_price = 0
last_news_text = ""

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

def get_news_text():
 try:
  if not FINNHUB_KEY: return "1. Crude market stable\n2. No major global event\n3. Dollar stable"
  r = requests.get(f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}", timeout=8).json()
  txt=""
  for i,n in enumerate(r[:3]): txt+=f"{i+1}. {n['headline'][:75]}\n"
  return txt.strip() if txt else "1. Market stable"
 except: return "1. OPEC update awaited\n2. US inventory data\n3. Global stable"

def color_fmt(change, label):
 if change > 0.10: return f"🟢 {label} (+{change:.2f}%)"
 elif change < -0.10: return f"🔴 {label} ({change:.2f}%)"
 else: return f"🔵 {label} ({change:.2f}% Stable)"

def make_hi_text():
 inr=get_inr()
 crude=get_data("CL=F"); nifty=get_data("^NSEI"); sensex=get_data("^BSESN"); bank=get_data("^NSEBANK")
 sp=get_data("^GSPC"); nas=get_data("^IXIC"); dow=get_data("^DJI")
 ftse=get_data("^FTSE"); dax=get_data("^GDAXI"); gold=get_data("GC=F")
 now=datetime.now(IST).strftime('%I:%M:%S %p, %d %b')
 news=get_news_text()
 emo="BULLISH STRONG 🟢" if crude and crude['change']>0.5 else "BEARISH 🔴" if crude and crude['change']<-0.5 else "STABLE 🔵"
 pred="Buying chal rahi hai" if crude and crude['change']>0 else "Selling pressure" if crude and crude['change']<0 else "Range me hai"

 t=f"📌 <b>PATIALA CRUDE LIVE - {now}</b>\n\n"
 if crude:
  t+=f"🛢️ <b>CRUDE OIL (WTI)</b>\n{color_fmt(crude['change'], f\"${crude['price']:.2f} (Rs {crude['price']*inr:,.0f})\")}\n"
  t+=f"High: ${crude['high']:.2f} (Rs {crude['high']*inr:,.0f}) Low: ${crude['low']:.2f} (Rs {crude['low']*inr:,.0f})\n"
  t+=f"Emotion: {emo}\nPrediction: {pred}\n\n"
 t+=f"🇮🇳 <b>INDIAN MARKET</b>\n"
 if nifty: t+=f"NIFTY: {color_fmt(nifty['change'], str(round(nifty['price'],2)))}\n"
 if sensex: t+=f"SENSEX: {color_fmt(sensex['change'], str(round(sensex['price'],2)))}\n"
 if bank: t+=f"BANKNIFTY: {color_fmt(bank['change'], str(round(bank['price'],2)))}\n\n"
 t+=f"🇺🇸 <b>USA</b> | 🇪🇺 <b>EUROPE</b>\n"
 if sp: t+=f"S&P: {color_fmt(sp['change'], str(round(sp['price'],2)))}\n"
 if nas: t+=f"NASDAQ: {color_fmt(nas['change'], str(round(nas['price'],2)))}\n"
 if ftse: t+=f"FTSE: {color_fmt(ftse['change'], str(round(ftse['price'],2)))}\n"
 if dax: t+=f"DAX: {color_fmt(dax['change'], str(round(dax['price'],2)))}\n\n"
 if gold:
  t+=f"💰 <b>GOLD:</b> {color_fmt(gold['change'], f\"${gold['price']:.2f} (Rs {gold['price']*inr*10:,.0f})\")}\n\n"
 t+=f"🗞️ <b>BREAKING NEWS</b>\n{news}\n\n<i>Silent Pin har 2 min | Alert = Sound ON</i>"
 return t

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hii','hello','status','/status'])
def hi_handler(m): bot.send_message(m.chat.id, make_hi_text())

@bot.message_handler(commands=['liveon','pinon'])
def liveon(m):
 global pinned_id
 msg=bot.send_message(GROUP_ID, make_hi_text())
 pinned_id=msg.message_id
 try: bot.pin_chat_message(GROUP_ID, pinned_id, disable_notification=True)
 except: pass

@bot.message_handler(commands=['liveoff'])
def liveoff(m):
 global pinned_id; pinned_id=None; bot.reply_to(m, "Pin OFF")

def smart_updater():
 global pinned_id, last_crude_price, last_news_text
 while True:
  try:
   time.sleep(120)
   inr=get_inr(); crude=get_data("CL=F")
   if not crude: continue
   if pinned_id:
    try: bot.edit_message_text(make_hi_text(), GROUP_ID, pinned_id)
    except: pass
   if last_crude_price!=0:
    diff=((crude['price']-last_crude_price)/last_crude_price*100)
    if abs(diff)>=0.70:
     bot.send_message(GROUP_ID, f"🚨 <b>SUDDEN {'HIGH' if diff>0 else 'LOW'}</b>\n🛢️ ${crude['price']:.2f} (Rs {crude['price']*inr:,.0f}) {diff:+.2f}%", disable_notification=False)
   last_crude_price=crude['price']
  except Exception as e:
   print(e); time.sleep(60)

threading.Thread(target=smart_updater, daemon=True).start()
while True:
 try:
  bot.infinity_polling(none_stop=True, timeout=90)
 except: time.sleep(10)
