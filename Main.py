import os, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v7.3 FINAL FIXED")
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
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004448478970"))
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
IST = pytz.timezone('Asia/Kolkata')
pinned_id = None

def get_inr():
 try:
  d = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()
  return d['rates']['INR']
 except:
  return 88.0

def get_data(sym):
 try:
  h = yf.Ticker(sym).history(period="2d")
  if h.empty: return None
  c = float(h["Close"].iloc[-1])
  p = float(h["Close"].iloc[-2]) if len(h)>1 else c
  ch = ((c-p)/p*100) if p else 0
  return {"price":c,"change":ch}
 except: return None

def get_technical_chance(sym="CL=F"):
  try:
    df = yf.Ticker(sym).history(period="6mo")
    if len(df) < 60: return 50, "STABLE_50", "STABLE_50"
    close = df["Close"]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]
    atr = (df["High"] - df["Low"]).rolling(14).mean().iloc[-1]
    price = close.iloc[-1]
    score = 20 if price > ma20 else 0
    if price > ma50: score+=20
    bullish_pct = max(20, min(80, 50+score))
    trend = "BULL_" + str(bullish_pct) if bullish_pct>=60 else "BEAR_" + str(100-bullish_pct) if bullish_pct<=40 else "STABLE_" + str(bullish_pct)
    return bullish_pct, trend, str(ma20)
  except Exception as e:
    print(f"Tech error {e}")
    return 50, "STABLE_50", "STABLE_50"

def get_news():
  try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=crude+oil+OPEC&hl=en-IN&gl=IN&ceid=IN:en")
    if feed.entries:
      txt = ""
      for i in range(3):
        h = feed.entries[i].title[:65].replace("<","").replace(">","")
        txt += str(i+1) + ". " + h + "\n"
      return txt
  except: pass
  return "1. OPEC supply in focus\n2. US inventory awaited\n3. Crude outlook stable"

def color_fmt(ch, label):
 if ch > 0.10: return "🟢 " + label + f" (+{ch:.2f}%)"
 if ch < -0.10: return "🔴 " + label + f" ({ch:.2f}%)"
 return "🔵 " + label + f" ({ch:.2f}% Stable)"

def get_nifty_plan_text():
  lines = [
    "<b>📌 NIFTY 50 - TRADE PLAN</b>",
    "<b>MONDAY • 12 OCT 2026</b> | Educational",
    "━━━━━━━━━━━━━━━━━━━━",
    "<b>⚡ FAST READ</b>",
    "🐂 LONG: 22,580 upar = LONG 22,600",
    "🐻 SHORT: 22,180 tode + 22,220 fail = SHORT",
    "<b>Make-or-Break = 22,180</b>",
    "━━━━━━━━━━━━━━━━━━━━",
    "<b>🎯 LEVELS</b>",
    "Res: 22,580 -> 22,600 -> 22,775 -> 22,950",
    "Sup: 22,400 -> 22,350 -> 22,220 -> 22,180 -> 22,000",
    "━━━━━━━━━━━━━━━━━━━━",
    "<b>PLAN A [9:30-11:00]</b> LONG 22,600 SL 22,480 TGT 22,775-22,950",
    "<b>PLAN B [9:30-12:30]</b> LONG 22,400 SL 22,140 TGT 22,580-22,775",
    "<b>PLAN C [Anytime]</b> SHORT 22,180 SL 22,340 TGT 22,000",
    "After 2:45 PM -> No New Trades"
  ]
  return "\n".join(lines)

def make_hi_text():
 inr = get_inr()
 crude = get_data("CL=F")
 nifty = get_data("^NSEI")
 bull_pct, trend_line, scalp_line = get_technical_chance("CL=F")
 now = datetime.now(IST).strftime('%I:%M %p, %d %b')
 news = get_news()
 msg = "<b>📌 PATIALA CRUDE LIVE - " + now + "</b>\n\n"
 if crude:
  label = "$" + str(round(crude['price'],2)) + " (Rs " + str(int(crude['price']*inr)) + ")"
  msg += "🛢️ <b>CR
