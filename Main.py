import os, threading, json
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK v5.6 DIRECT")
 def do_HEAD(self): self.send_response(200); self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get("PORT", 10000))
 HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

import time, pytz, requests, yfinance as yf, telebot, feedparser
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004448478970"))
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
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
 if any(x in hl for x in ["fall","falls","down","drops","slump","plunge","slash outlook","weak demand","surplus","build","rise in inventory","high","recession","demand down","strong dollar"]):
  return "🔴 BEARISH"
 if any(x in hl for x in ["cut","war","tension","attack","strike","disrupt","blast","embargo","sanction","draw","low inventory","reserve low"]):
  return "🟢 BULLISH"
 return "🔵 NEUTRAL"

def get_news():
  try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=crude+oil+OPEC+US+inventory&hl=en-IN&gl=IN&ceid=IN:en")
    if feed.entries and len(feed.entries)>=3:
      txt = ""
      for i in range(3):
        h = feed.entries[i].title[:65].replace("<","").replace(">","")
        txt += f"{i+1}. {h} {impact(h)}\n"
      return txt
  except: pass
  try:
    if FINNHUB_KEY and len(FINNHUB_KEY)>10:
      r = requests.get(f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}",timeout=5).json()
      if r and len(r)>=3:
        txt = ""
        for i in range(min(3,len(r))):
          h = r[i]['headline'][:65].replace("<","").replace(">","")
          txt += f"{i+1}. {h} {impact(h)}\n"
        return txt
  except: pass
  return "1. OPEC supply in focus - 🔵 NEUTRAL\n2. US inventory awaited - 🔵 NEUTRAL\n3. Crude demand outlook stable - 🔵 NEUTRAL"

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
  msg += f"Trend: {emo}\n\n"

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

 msg += f"\n🗞️ <b>NEWS</b>\n{news}\n"
 return msg

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hii','hello','status'])
def hi_handler(m): bot.send_message(m.chat.id, make_hi_text())

@bot.message_handler(commands=['alertwhen'])
def alertwhen_handler(m):
    try:
        txt = m.text.split()
        if len(txt) < 2:
            bot.reply_to(m, "Use: /alertwhen +10\n/alertwhen -10")
            return
        pct = float(txt[1].replace("%",""))
        if abs(pct) < 1 or abs(pct) > 50:
            bot.reply_to(m, "1% to 50% allowed"); return
        crude = get_data("CL=F")
        if not crude: bot.reply_to(m, "Price nahi mila, try later"); return
        base = crude['price']
        cid = str(m.chat.id)
        if cid not in alerts: alerts[cid] = []
        alerts[cid].append([pct, base])
        save_alerts()
        bot.reply_to(m, f"✅ Alert set: {pct}% {'UP' if pct>0 else 'DOWN'}\nBase: ${base:.2f} -> Target: ${base*(1+pct/100):.2f}")
    except:
        bot.reply_to(m, "Format: /alertwhen +10")

# --- DIRECT WITHOUT / ---
@bot.message_handler(func=lambda m: m.text and "alert when" in m.text.lower() or m.text and m.text.lower().startswith("alertwhen"))
def direct_alert_handler(m):
    try:
        if m.text.startswith("/"): return
        t = m.text.lower().replace("alert when", " alertwhen ").replace("alertwhen", " alertwhen ")
        parts = t.split()
        pct = None
        for p in parts:
            clean = p.replace("%","")
            try:
                if clean.replace("+","").replace("-","").replace(".","").isdigit() or (clean
