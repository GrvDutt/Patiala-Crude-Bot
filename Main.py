import os, threading, json, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v7.1 FORMATTED PLAN")
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
import pandas as pd
import numpy as np

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

def get_technical_chance(sym="CL=F"):
  try:
    df = yf.Ticker(sym).history(period="6mo")
    if len(df) < 60:
        return 50, "STABLE", "SIDEWAYS"
    close = df['Close']
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
    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
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
  except:
    return 50, "STABLE_50", "STABLE_50"

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
        if "RED" in imp: icon = "🔴 🐻 BEARISH"
        elif "GREEN" in imp: icon = "🟢 🐂 BULLISH"
        else: icon = "🔵 NEUTRAL"
        txt += f"{i+1}. {h} - {icon}\n"
      return txt
  except: pass
  return "1. OPEC supply in focus - 🔵 NEUTRAL\n2. US inventory awaited - 🔵 NEUTRAL\n3. Crude outlook stable - 🔵 NEUTRAL"

def color_fmt(ch, label):
 if ch > 0.10: return f"🟢 {label} (+{ch:.2f}%)"
 if ch < -0.10: return f"🔴 {label} ({ch:.2f}%)"
 return f"🔵 {label} ({ch:.2f}% Stable)"

# --- UPDATED FORMATTED PLAN WITH BOLD + SPACE + FAST READ ---
def get_nifty_plan_text():
  return """<b>📌 NIFTY 50 - TRADE PLAN</b>
<b>MONDAY • 12 OCT 2026</b> | Educational
━━━━━━━━━━━━━━━━━━━━

<b>⚡ FAST READ (10 Sec)</b>
🐂 <b>LONG tabhi jab:</b>
  → <code>22,580</code> ke upar tikke = LONG <code>22,600</code>
  → <code>22,350-22,400</code> hold kare = Dip Buy

🐻 <b>SHORT tabhi jab:</b>
  → <code>22,180</code> tode + <code>22,220</code> pe fail = SHORT

<b>Make-or-Break = 22,180</b>
Bada Trend = <b>BEARISH (200-EMA ke neeche)</b>

━━━━━━━━━━━━━━━━━━━━
<b>🔍 CONFLUENCE SNAPSHOT</b>

- <b>Structure:</b> 22,180 = Oct 8 low ≈ April low
  3-month low retest ho raha hai

- <b>Friday Close:</b> 22,520 (+340 pts)
  Buyers ne defend kiya 🟢

- <b>PCR/OI:</b> PCR 1.15
  Put OI 240M vs Call 207M = Defensive

- <b>ATM Straddle:</b> 205 (13 Oct)
  PE 152.7 > CE 134.8 = Put mehenga

- <b>Flows:</b>
  FII: -12,944 → -3,569 Cr = Selling slow 🟢
  DII: +10,703 / +4,743 Cr = Absorb

- <b>Global:</b>
  Nasdaq Fut +0.85% 🟢 | Brent -1.2% 🔴
  Opening Positive

━━━━━━━━━━━━━━━━━━━━
<b>🎯 KEY LEVELS</b>

<b>Resistance (Upar):</b>
  <code>22,580</code> → OR Breakout Trigger
  <code>22,600</code> → 🚀 LONG Entry
  <code>22,775</code> → Target 1
  <code>22,950</code> → Target 2

<b>Support (Neeche):</b>
  <code>22,400</code> → Dip-Buy Zone
  <code>22,350</code> → Lower Edge
  <code>22,220</code> → Failed Bounce
  <code>22,180</code> → 💥 Breakdown / SHORT Trigger
  <code>22,000</code> → Down Target

━━━━━━━━━━━━━━━━━━━━
<b>📋 ENTRY PLAN</b>

<b>9:15 - 9:30</b>
→ <b>NO TRADE</b> - Sirf OR High/Low mark karo

<b>PLAN A [9:30-11:00] - OR Breakout</b>
Gap-up + Above <code>22,580</code> sustain
→ <b>LONG 22,600</b>
  SL: <code>22,480</code>
  Target: <code>22,775 → 22,950</code>

<b>PLAN B [9:30-12:30] - Dip Buy</b>
<code>22,350-22,400</code> hold, neeche close nahi
→ <b>LONG 22,400</b>
  SL: <code>22,140</code>
  Target: <code>22,580 → 22,775</code>

<b>PLAN C [Anytime] - Breakdown</b>
Below <code>22,180</code> + bounce fail at <code>22,220</code>
→ <b>SHORT 22,180</b>
  SL: <code>22,340</code>
  Target: <code>22,000</code>

<b>After 2:45 PM → No New Trades (3:05 Square-off)</b>

━━━━━━━━━━━━━━━━━━━━
<b>⚡ GAME PLAN</b>
→ 22,180 major support
→ 22,580 ke upar hi long confirm
→ 22,350 hold tabhi dip-buy
→ Risk tight, SL mandatory
"""

def make_hi_text():
 inr = get_inr()
 crude = get_data("CL=F")
 nifty = get_data("^NSEI")
 sensex = get_data("^BSESN")
 sp = get_data("^GSPC")
 nas = get_data("^IXIC")
 gold = get_data("GC=F")
 bull_pct, trend_line, scalp_line = get_technical_chance("CL=F")
 now = datetime.now(IST).strftime('%I:%M %p, %d %b')
 news = get_news()
 msg = f"<b>📌 PATIALA CRUDE LIVE - {now}</b>\n\n"
 if crude:
  label = f"${crude['price']:.2f} (Rs {crude['price']*inr:,.0f})"
  msg += f"🛢️ <b>CRUDE OIL</b>\n"
  msg += color_fmt(crude['change'], label) + "\n"
  if "BULL_" in trend_line:
    bp = trend_line.split("_")[1]
    msg += f"Trend: 🐂 <b>BULLISH [Up {bp}% chance]</b>\n\n"
    sparts = scalp_line.split("_")
    msg += f"📊 <b>F&O SCALP:</b>\nBias: 🐂 BULLISH [{bp}% up]\nIdea: Dip pe CE Buy\nS1: <code>{sparts[2]}</code> | SL: <code>{sparts[3]}</code>\n\n"
  elif "BEAR_" in trend_line:
    bp = trend_line.split("_")[1]
    msg += f"Trend: 🐻 <b>BEARISH [Down {bp}% chance]</b>\n\n"
    sparts = scalp_line.split("_")
    msg += f"📊 <b>F&O SCALP:</b>\nBias: 🐻 BEARISH [{bp}% down]\nIdea: Bounce pe PE Buy\nR1: <code>{sparts[2]}</code> | SL: <code>{sparts[3]}</code>\n\n"
  else:
    parts = trend_line.split("_")
    b = parts[1] if len(parts)>1 else "50"
    br = parts[2] if len(parts)>2 else "50"
    msg += f"Trend: 🔵 <b>STABLE [Up {b}% / Down {br}%]</b>\n\n"
    msg += f"📊 <b>F&O SCALP:</b>\nBias: 🔵 SIDEWAYS\nIdea: Range scalp\n\n"
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
 msg += f"\n📰 <b>NEWS</b>\n{news}\n"
 msg += "\n💡 Type <b>'plan'</b> for NIFTY 50 Trade Plan"
 return msg

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hii','hello','status'])
def hi_handler(m): bot.send_message(m.chat.id, make_hi_text())

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['plan','nifty plan','trade plan','confluence','nifty50'])
def plan_handler(m): bot.send_message(m.chat.id, get_nifty_plan_text())

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
                    bot.send_message(int(cid), f"🚨 🐂 {sk.upper()} {pct}% UP HIT! {base:.2f} -> {curr:.2f}")
                    alerts[cid].remove(item)
                elif pct<0 and curr<=target:
                    bot.send_message(int(cid), f"🚨 🐻 {sk.upper()} {pct}% DOWN HIT! {base:.2f} -> {curr:.2f}")
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
     tag="HIGH 🐂" if diff>0 else "LOW 🐻"
     bot.send_message(GROUP_ID, f"🚨 SUDDEN {tag} {diff:+.2f}% ${crude['price']:.2f}")
   last_crude_price=crude['price']
  except: time.sleep(60)

threading.Thread(target=updater, daemon=True).start()
bot.infinity_polling(none_stop=True, timeout=90)
