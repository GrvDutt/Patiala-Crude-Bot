import os, threading, json, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v7.0 STAT ACCURATE + EMOJI + PLAN")
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

# --- UPDATED: More Statistically Accurate % Chance (Wilder RSI + EMA) ---
def get_technical_chance(sym="CL=F"):
  try:
    df = yf.Ticker(sym).history(period="6mo")
    if len(df) < 60:
        return 50, "🔵 STABLE [Up 50% chance]", "Bias: SIDEWAYS | Wait for confirmation"
    close = df['Close']
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1] if len(df)>200 else ma50
    price = close.iloc[-1]

    # Wilder RSI 14 (more accurate)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_now = float(rsi.iloc[-1])

    # MACD accurate
    ema12 = close.ewm(span=12, adjust=False).mean().iloc[-1]
    ema26 = close.ewm(span=26, adjust=False).mean().iloc[-1]
    ema12_series = close.ewm(span=12, adjust=False).mean()
    ema26_series = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12_series - ema26_series
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist_bull = float(macd_line.iloc[-1] - signal_line.iloc[-1]) > 0

    # Volume / Volatility filter
    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]

    score = 0
    if price > ma20: score+=18
    if price > ma50: score+=18
    if price > ma200: score+=10
    if ma20 > ma50: score+=12
    else: score-=12
    if macd_hist_bull: score+=18
    if 50 < rsi_now < 68: score+=20 # ideal bullish momentum
    elif rsi_now >= 68 and rsi_now < 78: score+=8 # overbought but strong
    elif rsi_now > 78: score-=5
    elif rsi_now > 42: score+=3
    elif rsi_now < 32: score-=12 # oversold

    bullish_pct = max(15, min(85, int(50 + score - 28)))
    bearish_pct = 100 - bullish_pct

    if bullish_pct >= 62:
        trend = f"🐂 BULLISH [Up {bullish_pct}% chance]"
        scalp = f"Bias: 🐂 BULLISH [{bullish_pct}% up]\nIdea: Dip pe CE Buy\nS1: {ma20:.2f} | SL: {ma50:.2f} | ATR: {atr:.2f}"
    elif bullish_pct <= 38:
        trend = f"🐻 BEARISH [Down {bearish_pct}% chance]"
        scalp = f"Bias: 🐻 BEARISH [{bearish_pct}% down]\nIdea: Bounce pe PE Buy\nR1: {ma20:.2f} | SL: {ma50:.2f} | ATR: {atr:.2f}"
    else:
        trend = f"🔵 STABLE [Up {bullish_pct}% / Down {bearish_pct}%]"
        scalp = f"Bias: 🔵 SIDEWAYS\nIdea: Range scalp\nS1: {ma50:.2f} R1: {ma20:.2f} | RSI: {rsi_now:.1f}"

    return bullish_pct, trend, scalp
  except:
    return 50, "🔵 STABLE [Up 50% chance]", "Bias: NEUTRAL"

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

# --- NEW: NIFTY PLAN ---
def get_nifty_plan_text():
  return """📌 NIFTY 50 — FULL CONFLUENCE & TRADE PLAN
MONDAY • 12 OCT 2026 | Educational

CONFLUENCE SNAPSHOT
• Structure: 22,180 (Oct 8 low) ≈ April low - 3-month low retest
• Friday close: 22,520 - Low 22,180 se +340 pts - buyers ne defend kiya
• PCR/OI: PCR 1.15 - Put OI 240M vs Call OI 207M - Put writers active
• ATM Straddle (Oct 13): 205 - PE 152.7 vs CE 134.85 - Put premium richer
• Flows: FII -12,944 → -3,569 Cr; DII +10,703 / +4,743 Cr - selling slow, DII absorb
• Global: Nasdaq fut +0.85% • Brent -1.2% - Opening positive, crude cool
• Trend: 1Y -10.9% • Below 200-EMA - Bada trend bearish, bounce ko reversal mat samjho

KEY LEVELS
Resistance: 22,950 (T2) - 22,775 (T1) - 22,600 (long trigger) - 22,580 (OR breakout) - 22,520 (Fri close)
Support: 22,400 (dip-buy) - 22,350 (lower edge) - 22,220 (failed bounce) - 22,180 (key low / breakdown) - 22,000 (down target)

MONDAY ENTRY PLAN
9:15-9:30 Any opening → NO TRADE - mark OR high/low
A 9:30-11:00 Gap-up / OR breakout above 22,580 → LONG 22,600 | SL 22,480 | Targets 22,775 → 22,950
B 9:30-12:30 Dip 22,350-22,400 holds, no close below → LONG 22,400 | SL 22,140 | Targets 22,580 → 22,775
C Anytime Break below 22,180 then bounce fails at 22,220 → SHORT 22,180 | SL 22,340 | Target 22,000
After 2:45 PM Any condition → No new trades, square off by 3:05 PM

QUICK GAME PLAN
• 22,180 = major make-or-break support
• 22,580 ke upar sustained breakout = long setup, confirmation zaroori
• 22,350-22,400 hold kare tabhi dip-buy
• 22,180 neeche + 22,220 rejection = short setup
• Trend below 200-EMA: risk tight rakho, SL mandatory
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
 msg = f"📌 PATIALA CRUDE LIVE - {now}\n\n"
 if crude:
  label = f"${crude['price']:.2f} (Rs {crude['price']*inr:,.0f})"
  msg += f"🛢️ CRUDE OIL\n"
  msg += color_fmt(crude['change'], label) + "\n"
  msg += f"Trend: {trend_line}\n\n"
  msg += f"📊 F&O SCALP:\n{scalp_line}\n\n"
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
 msg += f"\n📰 NEWS\n{news}\n"
 msg += "\n💡 Type 'plan' for NIFTY 50 Trade Plan"
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
