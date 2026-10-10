import os, threading, json, re, time
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v7.1 FIXED - 15 MIN MODE")
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get("PORT", 10000))
 HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

import pytz, requests, yfinance as yf, telebot, feedparser
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004448478970"))
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
IST = pytz.timezone('Asia/Kolkata')
pinned_id = None
last_crude_price = 0

ALERTS_FILE = "alerts.json"
alerts = {}
if os.path.exists(ALERTS_FILE):
    try: alerts = json.loads(open(ALERTS_FILE).read())
    except: alerts = {}

def save_alerts():
    try: open(ALERTS_FILE,"w").write(json.dumps(alerts))
    except: pass

SYMBOLS = {"crude":"CL=F","oil":"CL=F","nifty":"^NSEI","sensex":"^BSESN","sp":"^GSPC","nasdaq":"^IXIC","gold":"GC=F"}

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
  return {"price":c,"change":ch}
 except: return None

# --- SYNTAX FIX YAHAN KIYA HAI ---
def get_technical_chance(sym="CL=F"):
  try:
    df = yf.Ticker(sym).history(period="6mo")
    if len(df) < 60: return 50, "STABLE", "SIDEWAYS"
    close = df["Close"]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1] if len(df)>200 else ma50
    price = close.iloc[-1]
    delta = close.diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_now = float(rsi.iloc[-1])
    ema12_series = close.ewm(span=12, adjust=False).mean()
    ema26_series = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12_series - ema26_series
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist_bull = float(macd_line.iloc[-1] - signal_line.iloc[-1]) > 0
    # FIXED LINE - ab double quotes use kiye
    atr = (df["High"] - df["Low"]).rolling(14).mean().iloc[-1]
    score = 0
    if price > ma20: score+=18
    if price > ma50: score+=18
    if price > ma200: score+=10
    if ma20 > ma50: score+=12
    else: score-=12
    if macd_hist_bull: score+=18
    if 50 < rsi_now < 68: score+=20
    elif rsi_now >= 68 and rsi_now < 78: score+=8
    elif rsi_now > 78: score-=5
    elif rsi_now > 42: score+=3
    elif rsi_now < 32: score-=12
    bullish_pct = max(15, min(85, int(50 + score - 28)))
    bearish_pct = 100 - bullish_pct
    if bullish_pct >= 62:
        trend = f"BULL_{bullish_pct}"
        scalp = f"BULL_{bullish_pct}_{ma20:.2f}_{ma50:.2f}_{atr:.2f}_{rsi_now:.1f}"
    elif bullish_pct <= 38:
        trend = f"BEAR_{bearish_pct}"
        scalp = f"BEAR_{bearish_pct}_{ma20:.2f}_{ma50:.2f}_{atr:.2f}_{rsi_now:.1f}"
    else:
        trend = f"STABLE_{bullish_pct}_{bearish_pct}"
        scalp = f"STABLE_{bullish_pct}_{ma50:.2f}_{ma20:.2f}_{rsi_now:.1f}"
    return bullish_pct, trend, scalp
  except Exception as e:
    print(f"Technical error: {e}")
    return 50, "STABLE_50", "STABLE_50"

def impact(head):
 hl = head.lower()
 if any(x in hl for x in ["fall","falls","down","drops","slump","plunge","decline","weak","surplus","build","oversupply","recession","slowdown","slash","cut outlook"]): return "RED BEARISH"
 if any(x in hl for x in ["cut","war","tension","attack","strike","disrupt","blast","embargo","sanction","draw"]): return "GREEN BULLISH"
 return "BLUE NEUTRAL"

def get_news():
  try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=crude+oil+OPEC&hl=en-IN&gl=IN&ceid=IN:en")
    if feed.entries:
      txt = ""
      for i in range(3):
        h = feed.entries[i].title[:65].replace("<","").replace(">","")
        imp = impact(h)
        if "RED" in imp: icon = "🔴 🐻 BEARISH"
        elif "GREEN" in imp: icon = "🟢 🐂 BULLISH"
        else: icon = "🔵 NEUTRAL"
        txt += f"{i+1}. {h} - {icon}\n"
      return txt
  except:
