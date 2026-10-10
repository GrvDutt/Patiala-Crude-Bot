import os, threading, json, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK v5.9 CLEAN")
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

SYMBOLS = {
 "crude": "CL=F",
 "oil": "CL=F",
 "nifty": "^NSEI",
 "sensex": "^BSESN",
 "sp": "^GSPC",
 "nasdaq": "^IXIC",
 "gold": "GC=F"
}

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
        if "RED" in imp: icon = "🔴 BEARISH"
        elif "GREEN" in imp: icon = "🟢 BULLISH"
        else: icon = "🔵 NEUTRAL"
        txt += f"{i+1}. {h} - {icon}\n"
      return txt
  except: pass
  return "1. OPEC supply in focus - 🔵 NEUTRAL\n2. US inventory awaited - 🔵 NEUTRAL\n3. Crude outlook stable - 🔵 NEUTRAL"

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
 msg = f"📌 PATIALA CRUDE LIVE - {now}\n\n"
 if crude:
  label = f"${crude['price']:.2f} (Rs {crude['price']*inr:,.0f})"
  msg += f"CRUDE OIL\n"
  msg += color_fmt(crude['change'], label) + "\n"
  emo = "BULLISH 🟢" if crude['change']>0.5 else "BEARISH 🔴" if crude['change']<-0.5 else "STABLE 🔵"
  msg += f"Trend: {emo}\n\n"
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
def hi_handler(m): bot.send_message(m.chat.id, make_hi_text())

@bot.message_handler(commands=['alertwhen'])
def alertwhen_handler(m):
    try:
        txt = m.text.lower()
        sym_key = "crude"
        for k in SYMBOLS:
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
        for k in SYMBOLS:
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
        bot.reply_to(m, f"✅ {sym_key.upper()} Alert: {pct}% \nBase: {base:.2f} -> Target: {base*(1+pct/100):.2f}")
    except:
        pass

@bot.message_handler(commands=['myalerts','clearalerts'])
def list_handler(m):
    cid = str(m.chat.id)
    if "clear" in m.text:
        alerts[cid]=[]
        save_alerts()
        bot.reply_to(m,"Cleared")
        return
    if cid not in alerts or not alerts[cid]:
        bot.reply_to(m,"Koi alert nahi")
        return
    txt="Alerts:\n"
    for pct,base,sk,sym in alerts[cid]:
        txt+=f"- {sk.upper()} {pct}% {base:.2f}->{base*(1+pct/100):.2f}\n"
    bot.reply_to(m,txt)

@bot.message_handler(commands=['liveon','pinon'])
def liveon(m):
 global pinned_id
 msg = bot.send_message(GROUP_ID, make_hi_text())
 pinned_id = msg.message_id
 try: bot.pin_chat_message(GROUP_ID, pinned_id, disable_notification=True)
 except: pass

def check_alerts():
    try:
        for cid in list(alerts.keys()):
            for item in alerts[cid][:]:
                pct,base,sk,sym = item
                data = get_data(sym)
                if not data: continue
                curr = data['price']
                target = base*(1+pct/100)
                if pct>0 and curr>=target:
                    bot.send_message(int(cid), f"🚨 {sk.upper()} {pct}% UP HIT! {base:.2f} -> {curr:.2f}")
                    alerts[cid].remove(item)
                elif pct<0 and curr<=target:
                    bot.send_message(int(cid), f"🚨 {sk.upper()} {pct}% DOWN HIT! {base:.2f} -> {curr:.2f}")
                    alerts[cid].remove(item)
        save_alerts()
    except: pass

def updater():
 global pinned_id, last_crude_price
 while True:
  try:
   time.sleep(120)
   crude = get_data("CL=F")
   if not crude: continue
   if pinned_id:
    try: bot.edit_message_text(make_hi_text(), GROUP_ID, pinned_id)
    except: pass
   check_alerts()
   if last_crude_price!=0:
    diff = ((crude['price']-last_crude_price)/last_crude_price*100)
    if abs(diff)>=0.70:
     tag="HIGH" if diff>0 else "LOW"
     bot.send_message(GROUP_ID, f"🚨 SUDDEN {tag} {diff:+.2f}% ${crude['price']:.2f}")
   last_crude_price=crude['price']
  except: time.sleep(60)

threading.Thread(target=updater, daemon=True).start()
bot.infinity_polling(none_stop=True, timeout=90)
