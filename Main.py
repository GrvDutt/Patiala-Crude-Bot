import os, time, threading, pytz, requests
import yfinance as yf
import telebot
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Render health
class H(BaseHTTPRequestHandler):
 def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"v5.0 SMART PIN LIVE")
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
 try: return requests.get("https://open.er-api.com/v6/latest/USD", timeout=10).json()['rates']['INR']
 except: return 88.0

def get_data(sym):
 try:
  h = yf.Ticker(sym).history(period="2d")
  if h.empty: return None
  c=h['Close'].iloc[-1]; p=h['Close'].iloc[-2] if len(h)>1 else c
  ch=((c-p)/p*100) if p else 0
  return {"price":c,"high":h['High'].iloc[-1],"low":h['Low'].iloc[-1],"change":ch}
 except: return None

def get_news_text():
 try:
  if not FINNHUB_KEY: return "1. Crude market stable\n2. No major global event\n3. Dollar index stable"
  r=requests.get(f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}", timeout=10).json()
  txt=""
  for i, n in enumerate(r[:3]): txt+=f"{i+1}. {n['headline'][:75]}\n"
  return txt.strip()
 except: return "1. OPEC supply update awaited\n2. US inventory data\n3. Global market stable"

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
 pred="Buying chal rahi hai, upar jayega" if crude and crude['change']>0 else "Selling pressure hai" if crude and crude['change']<0 else "Range me hai"

 t=f"📌 <b>PATIALA CRUDE LIVE - {now}</b>\n\n"
 if crude:
  t+=f"🛢️ <b>CRUDE OIL (WTI)</b>\n{color_fmt(crude['change'], f\"${crude['price']:.2f} (₹{crude['price']*inr:,.0f})\")}\n"
  t+=f"High: ${crude
