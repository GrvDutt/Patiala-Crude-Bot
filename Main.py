import os, threading, json
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v8.0 FULL UPGRADE - LIVE")
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get("PORT", 10000))
 HTTPServer(("0.0.0.0", port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

import pytz, requests, yfinance as yf, telebot, feedparser
from datetime import datetime
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004448478970"))
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
IST = pytz.timezone("Asia/Kolkata")
pinned_id = None

ALERTS_FILE = "alerts.json"
alerts = {}
if os.path.exists(ALERTS_FILE):
 try:
  alerts = json.loads(open(ALERTS_FILE, "r").read())
 except:
  alerts = {}

def save_alerts():
 try:
  open(ALERTS_FILE, "w").write(json.dumps(alerts))
 except:
  pass

def get_inr():
 try:
  d = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()
  return d["rates"]["INR"]
 except:
  return 88.0

def get_data(sym):
 try:
  h = yf.Ticker(sym).history(period="2d")
  if h.empty:
   return None
  c = float(h["Close"].iloc[-1])
  p = float(h["Close"].iloc[-2]) if len(h)>1 else c
  ch = ((c-p)/p*100) if p else 0
  return {"price":c,"change":ch}
 except:
  return None

def color_fmt(ch, label):
 if ch > 0.10:
  return "🟢 " + label + " (+" + str(round(ch,2)) + "%)"
 if ch < -0.10:
  return "🔴 " + label + " (" + str(round(ch,2)) + "%)"
 return "🔵 " + label + " (" + str(round(ch,2)) + "% Stable)"

def get_technical_chance(sym="CL=F"):
  try:
    df = yf.Ticker(sym).history(period="6mo")
    if len(df) < 60:
     return 50, "STABLE", 0, 0, 50, 0
    close = df["Close"]
    ma20 = float(close.rolling(20).mean().iloc[-1])
    ma50 = float(close.rolling(50).mean().iloc[-1])
    ma200 = float(close.rolling(200).mean().iloc[-1]) if len(df)>200 else ma50
    price = float(close.iloc[-1])
    delta = close.diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_now = float(rsi.iloc[-1])
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_bull = float(macd_line.iloc[-1] - signal_line.iloc[-1]) > 0
    atr = float((df["High"] - df["Low"]).rolling(14).mean().iloc[-1])
    score = 0
    if price > ma20: score+=18
    if price > ma50: score+=18
    if price > ma200: score+=10
    if ma20 > ma50: score+=12
    else: score-=8
    if macd_bull: score+=18
    if 50 < rsi_now < 68: score+=20
    elif rsi_now >= 68 and rsi_now < 78: score+=8
    elif rsi_now > 78: score-=5
    elif rsi_now > 42: score+=3
    elif rsi_now < 32: score-=10
    bullish_pct = max(15, min(85, int(50 + score - 28)))
    if bullish_pct >= 60:
     trend = "BULLISH"
    elif bullish_pct <= 40:
     trend = "BEARISH"
    else:
     trend = "STABLE"
    return bullish_pct, trend, ma20, ma50, rsi_now, atr
  except Exception as e:
    print("Tech error", e)
    return 50, "STABLE", 0, 0, 50, 0

def impact(head):
 hl = head.lower()
 if any(x in hl for x in ["fall","
