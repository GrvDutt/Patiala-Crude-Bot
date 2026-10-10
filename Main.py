import os, time, threading, pytz, requests, random
import yfinance as yf
import telebot
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- RENDER LIVE SERVER (Band nahi hoga) ---
class H(BaseHTTPRequestHandler):
 def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"Bot v4.0 Live")
 def log_message(self, *a): pass
def run_server():
 try: HTTPServer(('0.0.0.0', int(os.environ.get("PORT",10000))), H).serve_forever()
 except: pass
threading.Thread(target=run_server, daemon=True).start()

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004448478970"))
ALERT_PERCENT = 0.5
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
# ---------------------------------

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
IST = pytz.timezone('Asia/Kolkata')
last_prices = {}
last_news = ""

def get_inr():
 try:
  r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10).json()
  return r['rates']['INR']
 except: return 88.0

def get_data(symbol):
 try:
  h = yf.Ticker(symbol).history(period="2d")
  if h.empty: return None
  curr = h['Close'].iloc[-1]; prev = h['Close'].iloc[-2] if len(h)>1 else curr
  return {"price":curr,"prev":prev,"high":h['High'].iloc[-1],"low":h['Low'].iloc[-1],"avg":h['Close'].mean(),"change":((curr-prev)/prev*100)}
 except: return None

def get_crude_full():
 try:
  ticker = yf.Ticker("CL=F")
  d = ticker.history(period="5d")
  h1 = ticker.history(period="2d", interval="1h")
  if d.empty: return None
  curr = d['Close'].iloc[-1]; prev = d['Close'].iloc[-2] if len(d)>1 else curr
  day_high = d['High'].iloc[-1]; day_low = d['Low'].iloc[-1]; day_avg = d['Close'].tail(24).mean() if len(d)>=1 else curr
  # Last 1 hour
  last_hour_change = 0; last_hour_price = curr
  if len(h1)>=2:
   last_hour_price = h1['Close'].iloc[-2]
   last_hour_change = ((curr-last_hour_price)/last_hour_price*100)
  # Week trend (5 day)
  week_start = d['Close'].iloc[0]; week_change = ((curr-week_start)/week_start*100)
  return {"price":curr,"prev":prev,"high":day_high,"low":day_low,"avg":day_avg,"change":((curr-prev)/prev*100),"lh_price":last_hour_price,"lh_change":last_hour_change,"week_change":week_change}
 except: return None

def get_nichod():
 if not OPENAI_KEY: return "Market stable, no panic."
 try:
  import openai
  client = openai.OpenAI(api_key=OPENAI_KEY)
  resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":"Crude oil news ka 1 line me nichod de - bullish/bearish/panic?"}], max_tokens=60)
  return resp.choices[0].message.content
 except: return "Global cues mixed, trend sideways."

HELP_TEXT = """
<b>📜 AVAILABLE COMMANDS</b>

<b>/status</b> - 🛢️ Crude Full Report (Same format)
<b>/ind</b> - 🇮🇳 Nifty, Sensex, BankNifty Trend
<b>/us</b> - 🇺🇸 USA Stocks Live
<b>/sum</b> - 🌍 Global Summary (Nifty+US+Crude+Gold)
<b>/all</b> - 💥 Sab kuch ek baar me
<b>?</b> ya <b>/?</b> - Ye list

<b>Auto Alerts:</b> Open/Close + Sudden High/Low + Breaking News (Ringtone ON)
"""

@bot.message_handler(commands=['start','help','commands'])
@bot.message_handler(func=lambda m: m.text and m.text.strip() in ['?','/?'])
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(commands=['status'])
def status_cmd(m):
 inr=get_inr(); d=get_crude_full()
 if not d: return
 trend = "BULLISH 🟢🔼" if d['change']>0 else "BEARISH 🔴🔽"
 lh_trend = "🟢" if d['lh_change']>0 else "🔴"
 week_trend = "🟢 UP" if d['week_change']>0 else "🔴 DOWN"
 nichod = get_nichod()
 msg = f"<b>📊 CRUDE TOTAL STATUS</b>\n\n<b>1. CURRENT:</b> {trend}\n<code>Live: ${d['price']:.2f} | ₹{d['price']*inr:,.0f}</code>\n<code>Open: ${d['prev']:.2f} | ₹{d['prev']*inr:,.0f}</code>\n<code>Trend: {d['change']:.2f}% {trend}</code>\n\n<b>2. LAST 1 HOUR:</b> {lh_trend} {d['lh_change']:.2f}%\n<code>Price: ${d['lh_price']:.2f}</code>\n\n<b>3. KAL KA:</b>\n<code>High: ${d['high']:.2f} | ₹{d['high']*inr:,.0f}</code>\n<code>Low: ${d['low']:.2f} | ₹{d['low']*inr:,.0f}</code>\n<code>Avg: ${d['avg']:.2f} | ₹{d['avg']*inr:,.0f}</code>\n\n<b>4. WEEK TREND:</b> {week_trend} ({d['week_change']:.2f}%)\n\n<b>5. NICHOD:</b> {nichod}"
 bot.reply_to(m, msg)

@bot.message_handler(commands=['ind'])
def ind_cmd(m):
 nifty=get_data("^NSEI"); sensex=get_data("^BSESN"); bank=get_data("^NSEBANK")
 msg=f"<b>🇮🇳 INDIAN MARKET TREND - {datetime.now(IST).strftime('%I:%M %p')}</b>\n\n"
 if nifty: msg+=f"NIFTY: <b>{nifty['price']:.2f}</b> ({nifty['change']:.2f}%) {'🟢' if nifty['change']>0 else '🔴'}\nHigh: {nifty['high']:.2f} Low: {nifty['low']:.2f}\n\n"
 if sensex: msg+=f"SENSEX: <b>{sensex['price']:.2f}</b> ({sensex['change']:.2f}%) {'🟢' if sensex['change']>0 else '🔴'}\n\n"
 if bank: msg+=f"BANKNIFTY: <b>{bank['price']:.2f}</b> ({bank['change']:.2f}%) {'🟢' if bank['change']>0 else '🔴'}\n"
 bot.reply_to(m, msg)

@bot.message_handler(commands=['us'])
def us_cmd(m):
 sp=get_data("^GSPC"); nas=get_data("^IXIC"); dow=get_data("^DJI")
 msg=f"<b>🇺🇸 USA STOCKS CURRENT</b>\n\n"
 if sp: msg+=f"S&P 500: <b>{sp['price']:.2f}</b> ({sp['change']:.2f}%) {'🟢' if sp['change']>0 else '🔴'}\n"
 if nas: msg+=f"NASDAQ: <b>{nas['price']:.2f}</b> ({nas['change']:.2f}%) {'🟢' if nas['change']>0 else '🔴'}\n"
 if dow: msg+=f"DOW: <b>{dow['price']:.2f}</b> ({dow['change']:.2f}%) {'🟢' if dow['change']>0 else '🔴'}\n"
 bot.reply_to(m, msg)

@bot.message_handler(commands=['sum','all'])
def all_cmd(m):
 inr=get_inr(); crude=get_crude_full(); gold=get_data("GC=F"); nifty=get_data("^NSEI"); sp=get_data("^GSPC")
 msg=f"<b>🌍 ALL MARKET SUMMARY - {datetime.now(IST).strftime('%d %b %I:%M %p')}</b>\n\n"
 if nifty: msg+=f"🇮🇳 NIFTY: {nifty['price']:.2f} ({nifty['change']:.2f}%) {'🟢' if nifty['change']>0 else '🔴'}\n"
 if sp: msg+=f"🇺🇸 S&P500: {sp['price']:.2f} ({sp['change']:.2f}%) {'🟢' if sp['change']>0 else '🔴'}\n"
 if crude: msg+=f"🛢️ CRUDE: <b>${crude['price']:.2f} | ₹{crude['price']*inr:,.0f}</b> ({crude['change']:.2f}%)\n"
 if gold: msg+=f"🥇 GOLD: ${gold['price']:.2f} ({gold['change']:.2f}%)\n"
 msg+=f"\nTrend: <b>{'🟢 Overall BULLISH' if crude and crude['change']>0 else '🔴 Overall BEARISH'}</b>"
 bot.reply_to(m, msg)

# --- AUTO SEND WITH RINGTONE ---
def send_auto(text):
 try: bot.send_message(GROUP_ID, text, disable_notification=False)
 except Exception as e: print(f"Auto err {e}")

def scheduled_checker():
 sent_today=set()
 while True:
  try:
   now=datetime.now(IST); ct=now.strftime("%H:%M"); today=now.strftime("%Y-%m-%d")
   if ct=="09:20" and f"{today}_ind_open" not in sent_today:
    d=get_data("^NSEI")
    if d: send_auto(f"<b>🇮🇳 MARKET OPEN - 9:20 AM</b>\n\nNIFTY: <b>{d['price']:.2f}</b> ({d['change']:.2f}%) {'🟢' if d['change']>0 else '🔴'}\nAaj ka trend: <b>{'UP' if d['change']>0 else 'DOWN'}</b>\n\nGood Morning Traders! ☀️")
    sent_today.add(f"{today}_ind_open")
   if ct=="13:35" and f"{today}_eu_open" not in sent_today:
    d=get_data("^GDAXI")
    if d: send_auto(f"<b>🇪🇺 EUROPE OPEN - 1:35 PM</b>\n\nDAX: <b>{d['price']:.2f}</b> ({d['change']:.2f}%)\n30 Min Trend: {'🟢 UP' if d['change']>0 else '🔴 DOWN'}")
    sent_today.add(f"{today}_eu_open")
   if ct=="19:05" and f"{today}_us_open1" not in sent_today:
    d=get_data("^GSPC")
    if d: send_auto(f"<b>🇺🇸 US OPEN - First 30 Min Trend</b>\n\nS&P500: <b>{d['price']:.2f}</b> ({d['change']:.2f}%)\nOpening Trend: <b>{'🔥 TEZ UP' if d['change']>0.5 else '🔴 DOWN' if d['change']<0 else 'Sideways'}</b>")
    sent_today.add(f"{today}_us_open1")
   if ct=="19:20" and f"{today}_us_open2" not in sent_today:
    d=get_data("^GSPC")
    if d: send_auto(f"<b>🇺🇸 US UPDATE - 15 Min Baad</b>\n\nAbhi ka Trend: <b>{d['change']:.2f}%</b> {'🟢' if d['change']>0 else '🔴'}")
    sent_today.add(f"{today}_us_open2")
   if ct=="15:40" and f"{today}_ind_close" not in sent_today:
    d=get_data("^NSEI")
    if d: send_auto(f"<b>🇮🇳 MARKET CLOSE - All Day Summary</b>\n\nClose: <b>{d['price']:.2f}</b>\nDay High: {d['high']:.2f}\nDay Low: {d['low']:.2f}\nDay Avg: {d['avg']:.2f}\nTrend: <b>{'🟢 BULLISH' if d['change']>0 else '🔴 BEARISH'}</b>")
    sent_today.add(f"{today}_ind_close")
   if ct=="01:30" and f"{today}_us_close" not in sent_today:
    d=get_data("^GSPC")
    if d: send_auto(f"<b>🇺🇸 US CLOSE - All Day Trend</b>\n\nClose: <b>{d['price']:.2f}</b>\nHigh: {d['high']:.2f} | Low: {d['low']:.2f}\nAvg: {d['avg']:.2f}\nFinal: {'🟢 UP DAY' if d['change']>0 else '🔴 DOWN DAY'}")
    sent_today.add(f"{today}_us_close")
   time.sleep(30)
  except Exception as e:
   print(f"Sched err {e}"); time.sleep(60)

def sudden_alert_checker():
 while True:
  try:
   for sym,name in [("CL=F","CRUDE"),("^NSEI","NIFTY"),("GC=F","GOLD")]:
    d=get_data(sym)
    if not d: continue
    last=last_prices.get(sym)
    if last:
     diff=abs((d['price']-last)/last*100)
     if diff>=ALERT_PERCENT:
      emoji="🚨🚨" if diff>1 else "⚠️"
      send_auto(f"{emoji} <b>HIGH ALERT - {name} {diff:.2f}% {'HIGH' if d['price']>last else 'LOW'}</b> {emoji}\n\n<b>{name} SUDDEN {'🔥 HIGH' if d['price']>last else '💥 LOW'}</b>\nPrice: <b>${d['price']:.2f}</b>\nChange: <b>{diff:.2f}% in 1 min</b>\nTrend: {'🟢🟢 UP' if d['price']>last else '🔴🔴 DOWN'}")
    last_prices[sym]=d['price']
   time.sleep(60)
  except: time.sleep(60)

def breaking_news_checker():
 global last_news
 while True:
  try:
   # Simple news check via yfinance
   n = yf.Ticker("CL=F").news
   if n:
    title = n[0].get('title','')
    if title and title!=last_news and any(k in title.lower() for k in ['war','opec','inventory','attack','sanction','crude']):
     last_news=title
     send_auto(f"⚠️ <b>BREAKING NEWS - CRUDE ALERT</b> ⚠️\n\n<b>{title}</b>\n\nTrend Check Karo! 🛢️")
   time.sleep(300)
  except: time.sleep(300)

threading.Thread(target=scheduled_checker, daemon=True).start()
threading.Thread(target=sudden_alert_checker, daemon=True).start()
threading.Thread(target=breaking_news_checker, daemon=True).start()

while True:
 try:
  print("Bot v4.0 FINAL Polling ON...")
  bot.infinity_polling(none_stop=True, timeout=90, long_polling_timeout=90)
 except Exception as e:
  print(f"Crash restart 10s: {e}"); time.sleep(10)
