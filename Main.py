import os, threading, json, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v6.2 FIXED")
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a):
  pass

def run_health():
 port = int(os.environ.get("PORT", 10000))
 HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

import time, pytz, requests, yfinance as yf, telebot, feedparser
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
 try:
  alerts = json.loads(open(ALERTS_FILE).read())
 except:
  alerts = {}
def save_alerts():
 try:
  open(ALERTS_FILE,"w").write(json.dumps(alerts))
 except:
  pass

SYMBOLS = {"crude":"CL=F","oil":"CL=F","nifty":"^NSEI","sensex":"^BSESN","sp":"^GSPC","nasdaq":"^IXIC","gold":"GC=F"}

def get_inr():
 try:
  return requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()['rates']['INR']
 except:
  return 88.0

def get_data(sym):
 try:
  h = yf.Ticker(sym).history(period="2d")
  if h.empty:
   return None
  c = float(h['Close'].iloc[-1])
  p = float(h['Close'].iloc[-2]) if len(h)>1 else c
  ch = ((c-p)/p*100) if p else 0
  return {"price":c,"change":ch}
 except:
  return None

def get_technical_chance(sym="CL=F"):
 try:
  df = yf.Ticker(sym).history(period="3mo")
  if len(df) < 50:
   return 50, "STABLE 🔵 [Up 50% chance]", "Bias: SIDEWAYS"
  close = df['Close']
  ma20 = close.rolling(20).mean().iloc[-1]
  ma50 = close.rolling(50).mean().iloc[-1]
  ma200 = close.rolling(200).mean().iloc[-1] if len(df)>200 else ma50
  price = close.iloc[-1]
  delta = close.diff()
  gain = (delta.where(delta>0,0)).rolling(14).mean()
  loss = (-delta.where(delta<0,0)).rolling(14).mean()
  rs = gain / loss
  rsi = 100 - (100 / (1 + rs))
  rsi_now = float(rsi.iloc[-1])
  ema12 = close.ewm(span=12).mean().iloc[-1]
  ema26 = close.ewm(span=26).mean().iloc[-1]
  macd_bull = ema12 > ema26
  score = 0
  if price > ma20:
   score+=20
  if price > ma50:
   score+=20
  if price > ma200:
   score+=10
  if ma20 > ma50:
   score+=15
  else:
   score-=10
  if macd_bull:
   score+=15
  if 55 < rsi_now < 70:
   score+=20
  elif rsi_now > 70:
   score+=10
  elif rsi_now > 45:
   score+=5
  elif rsi_now < 35:
   score-=10
  bullish_pct = max(15, min(85, 50 + score - 30))
  bearish_pct = 100 - bullish_pct
  if bullish_pct > 60:
   trend = f"BULLISH 🟢 [Up {bullish_pct}% chance]"
   scalp = f"Bias: BULLISH [{bullish_pct}% up]\nIdea: Dip pe CE Buy\nS1: {ma20:.2f} | SL: {ma50:.2f}"
  elif bullish_pct < 40:
   trend = f"BEARISH 🔴 [Down {bearish_pct}% chance]"
   scalp = f"Bias: BEARISH [{bearish_pct}% down]\nIdea: Bounce pe PE Buy\nR1: {ma20:.2f} | SL: {ma50:.2f}"
  else:
   trend = f"STABLE 🔵 [Up {bullish_pct}% / Down {bearish_pct}%]"
   scalp = f"Bias: SIDEWAYS\nIdea: Range scalp\nS1: {ma50:.2f} R1: {ma20:.2f}"
  return bullish_pct, trend, scalp
 except:
  return 50, "STABLE 🔵 [Up 50% chance]", "Bias: NEUTRAL"

def impact(head):
 hl = head.lower()
 if any(x in hl for x in ["fall","falls","down","drops","slump","plunge","decline","weak","surplus","build","oversupply","recession","slowdown","slash","cut outlook"]):
  return "RED BEARISH"
 if any(x in hl for x in ["cut","war","tension","attack","strike","disrupt","blast","embargo","sanction","draw"]):
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
     icon = "🔴 BEARISH"
    elif "GREEN" in imp:
     icon = "🟢 BULLISH"
    else:
     icon = "🔵 NEUTRAL"
    txt += f"{i+1}. {h} - {icon}\n"
   return txt
 except:
  pass
 return "1. OPEC supply in focus - 🔵 NEUTRAL\n2. US inventory awaited - 🔵 NEUTRAL\n3. Crude outlook stable - 🔵 NEUTRAL"

def color_fmt(ch, label):
 if ch > 0.10:
  return f"🟢 {label} (+{ch:.2f}%)"
 if ch < -0.10:
  return f"🔴 {label} ({ch:.2f}%)"
 return f"🔵 {label} ({ch:.2f}% Stable)"

def make_hi_text():
 inr = get_inr()
 crude = get_data("CL=F")
 nifty = get_data("^NSEI")
 sensex = get_data("^BSESN")
 sp = get_data("^GSPC")
 nas = get_data("^IXIC")
 gold = get_data("GC=F")
 _, trend_with_pct, scalp_text = get_technical_chance("CL=F")
 now = datetime.now(IST).strftime('%I:%M %p, %d %b')
 news = get_news()
 msg = f"📌 PATIALA CRUDE LIVE - {now}\n\n"
 if crude:
  label = f"${crude['price']:.2f} (Rs {crude['price']*inr:,.0f})"
  msg += f"CRUDE OIL\n"
  msg += color_fmt(crude['change'], label) + "\n"
  msg += f"Trend: {trend_with_pct}\n\n"
  msg += f"📊 F&O SCALP:\n{scalp_text}\n\n"
 if nifty:
  msg += f"NIFTY: {color_fmt(nifty['change'], str(round(nifty['price'],2)))}\n"
 if sensex:
  msg += f"SENSEX: {color_fmt(sensex['change'], str(round(sensex['price'],2)))}\n"
 if sp:
  msg += f"S&P: {color_fmt(sp['change'], str(round(sp['price'],2)))}\n"
 if nas:
  msg += f"NASDAQ: {color_fmt(nas['change'], str(round(nas['price'],2)))}\n"
 if gold:
  g_label = f"${gold['price']:.2f}"
  msg += f"GOLD: {color_fmt(gold['change'], g_label)}\n"
 msg += f"\nNEWS\n{news}\n"
 return msg

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hii','hello','status'])
def hi_handler(m):
 bot.send_message(m.chat.id, make_hi_text())

@bot.message_handler(commands=['alertwhen'])
def alertwhen_handler(m):
 try:
  txt = m.text.lower()
  sym_key = "crude"
  for k in SYMBOLS.keys():
   if k in txt:
    sym_key = k
    break
  match = re.search(r'([+-]?\d+(\.\d+)?)\s*%?', txt)
  if not match:
   bot.reply_to(m, "Use: /alertwhen crude +0.41")
   return
  pct = float(match.group(1))
  if abs(pct) < 0.1 or abs(pct) > 50:
   bot.reply_to(m, "0.1% to 50% allowed")
   return
  sym = SYMBOLS.get(sym_key, "CL=F")
  data = get_data(sym)
  if not data:
   bot.reply_to(m, "Price nahi mila")
   return
  base = data['price']
  cid = str(m.chat.id)
  if cid not in alerts:
   alerts[cid] = []
  alerts[cid].append([pct, base, sym_key, sym])
  save_alerts()
  bot.reply_to(m, f"✅ {sym_key.upper()} Alert: {pct}% UP\nBase: {base:.2f} -> Target: {base*(1+pct/100):.2f}")
 except:
  bot.reply_to(m, "Format: /alertwhen +0.41")

@bot.message_handler(func=lambda m: m.text and ("alert when" in m.text.lower() or m.text.lower().strip().startswith("alertwhen")))
def direct_alert_handler(m):
 try:
  if m.text.startswith("/"):
   return
  low = m.text.lower()
  sym_key = "crude"
  for k in SYMBOLS.keys():
   if k in low:
    sym_key = k
    break
  match = re.search(r'([+-]?\d+(\.\d+)?)\s*%?', low)
  if not match:
   return
  pct = float(match.group(1))
  if abs(pct) < 0.1 or abs(pct) > 50:
   return
  sym = SYMBOLS.get(sym_key, "CL=F")
  data = get_data(sym)
  if not data:
   return
  base = data['price']
  cid = str(m.chat.id)
  if cid not in alerts:
   alerts[cid] = []
  alerts[cid].append([pct, base, sym_key, sym])
  save_alerts()
  bot.reply_to(m, f"✅ {sym_key.upper()} Alert: {pct}% \nBase:
