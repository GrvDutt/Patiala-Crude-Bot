import os, threading, json, re, time
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v7.2 FINAL 15 MIN - FIXED")
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a):
  pass

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

def get_inr():
 try:
  r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()
  return r['rates']['INR']
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

def get_technical_chance(sym="CL=F"):
  try:
    df = yf.Ticker(sym).history(period="6mo")
    if len(df) < 60:
        return 50, "STABLE_50", "STABLE_50"
    close = df["Close"]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]
    atr = (df["High"] - df["Low"]).rolling(14).mean().iloc[-1]
    price = close.iloc[-1]
    score = 0
    if price > ma20:
     score+=20
    if price > ma50:
     score+=20
    bullish_pct = max(20, min(80, 50+score))
    trend = f"BULL_{bullish_pct}" if bullish_pct>=60 else f"BEAR_{100-bullish_pct}" if bullish_pct<=40 else f"STABLE_{bullish_pct}_{100-bullish_pct}"
    scalp = f"{trend}_{ma20:.2f}_{ma50:.2f}_{atr:.2f}"
    return bullish_pct, trend, scalp
  except Exception as e:
    print(f"Tech error: {e}")
    return 50, "STABLE_50", "STABLE_50"

def impact(head):
 hl = head.lower()
 if any(x in hl for x in ["fall","down","drops","weak","surplus"]):
  return "RED BEARISH"
 if any(x in hl for x in ["cut","war","tension","attack","disrupt"]):
  return "GREEN BULLISH"
 return "BLUE NEUTRAL"

def get_news():
  try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=crude+oil+OPEC&hl=en-IN&gl=IN&ceid=IN:en")
    if feed.entries:
      txt = ""
      for i in range(3):
        h = feed.entries[i].title[:65].replace("<","").replace(">","")
        imp = impact(h)
        if "RED" in imp:
         icon = "🔴 🐻 BEARISH"
        elif "GREEN" in imp:
         icon = "🟢 🐂 BULLISH"
        else:
         icon = "🔵 NEUTRAL"
        txt += f"{i+1}. {h} - {icon}\n"
      return txt
  except Exception as e:
    print(f"News error: {e}")
  return "1. OPEC supply in focus - 🔵 NEUTRAL\n2. US inventory awaited - 🔵 NEUTRAL\n3. Crude outlook stable - 🔵 NEUTRAL"

def color_fmt(ch, label):
 if ch > 0.10:
  return f"🟢 {label} (+{ch:.2f}%)"
 if ch < -0.10:
  return f"🔴 {label} ({ch:.2f}%)"
 return f"🔵 {label} ({ch:.2f}% Stable)"

def get_nifty_plan_text():
  return """<b>📌 NIFTY 50 - TRADE PLAN</b>
<b>MONDAY • 12 OCT 2026</b> | Educational
━━━━━━━━━━━━━━━━━━━━
