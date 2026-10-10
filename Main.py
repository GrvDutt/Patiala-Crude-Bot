import os, threading, json
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v8.5 ULTRA SAFE LIVE")
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

ALERTS_FILE = 'alerts.json'
alerts = {}
if os.path.exists(ALERTS_FILE):
 try:
  alerts = json.loads(open(ALERTS_FILE, 'r').read())
 except:
  alerts = {}

def save_alerts():
 try:
  open(ALERTS_FILE, 'w').write(json.dumps(alerts))
 except:
  pass

def get_inr():
 try:
  d = requests.get('https://open.er-api.com/v6/latest/USD', timeout=5).json()
  return d['rates']['INR']
 except:
  return 88.0

def get_data(sym):
 try:
  h = yf.Ticker(sym).history(period='2d')
  if h.empty:
   return None
  c = float(h['Close'].iloc[-1])
  p = float(h['Close'].iloc[-2]) if len(h)>1 else c
  ch = ((c-p)/p*100) if p else 0
  return {'price':c,'change':ch}
 except:
  return None

def color_fmt(ch, label):
 if ch > 0.10:
  return '[UP] ' + label + ' (+' + str(round(ch,2)) + '%)'
 if ch < -0.10:
  return '[DOWN] ' + label + ' (' + str(round(ch,2)) + '%)'
 return '[STABLE] ' + label + ' (' + str(round(ch,2)) + '%)'

def get_technical_chance(sym='CL=F'):
  try:
    df = yf.Ticker(sym).history(period='6mo')
    if len(df) < 60:
     return 50, 'STABLE', 0, 0, 50, 0
    close = df['Close']
    ma20 = float(close.rolling(20).mean().iloc[-1])
    ma50 = float(close.rolling(50).mean().iloc[-1])
    price = float(close.iloc[-1])
    delta = close.diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_now = float(rsi.iloc[-1])
    atr = float((df['High'] - df['Low']).rolling(14).mean().iloc[-1])
    bullish_pct = 50
    if price > ma20: bullish_pct+=10
    if price > ma50: bullish_pct+=10
    if rsi_now > 50: bullish_pct+=10
    bullish_pct = max(15, min(85, bullish_pct))
    trend = 'BULLISH' if bullish_pct>=60 else 'BEARISH' if bullish_pct<=40 else 'STABLE'
    return bullish_pct, trend, ma20, ma50, rsi_now, atr
  except:
    return 50, 'STABLE', 0, 0, 50, 0

def impact(head):
 hl = head.lower()
 red_words = ['fall','down','drops','plunge','decline','selloff','tariff','sanction','attack','missile','war']
 green_words = ['rally','buying','ceasefire','peace','stimulus','cut']
 if any(x in hl for x in red_words):
  return 'RED BEARISH'
 if any(x in hl for x in green_words):
  return 'GREEN BULLISH'
 return 'NEUTRAL'

def get_rss_news(query, limit=2):
  try:
    url = 'https://news.google.com/rss/search?q=' + query + '&hl=en-IN&gl=IN&ceid=IN:en'
    feed = feedparser.parse(url)
    txt = ''
    if feed.entries:
      for i in range(min(limit, len(feed.entries))):
        h = feed.entries[i].title[:80].replace('<','').replace('>','').replace("'","").replace('"','')
        imp = impact(h)
        txt += str(i+1) + '. ' + h + ' [' + imp + ']\n'
    return txt
  except:
    return ''

def get_world_leaders_impact():
  queries = ['US President tariff trade','Putin Russia Ukraine war','Xi Jinping China Taiwan','Netanyahu Israel Iran attack','OPEC Saudi oil cut','missile attack Middle East']
  final_txt = ''
  for q in queries:
    t = get_rss_news(q, 1)
    if t:
      final_txt += t
  return final_txt[:600]

def get_market_variables():
  try:
    vix = get_data('^INDIAVIX')
    usdinr = get_data('INR=X')
    txt = ''
    if vix:
      txt += 'VIX: ' + str(round(vix['price'],2)) + '\n'
    if usdinr:
      txt += 'USD INR: ' + str(round(usdinr['price'],2)) + '\n'
    return txt
  except:
    return ''

def make_hi_text():
 inr = get_inr()
 crude = get_data('CL=F')
 nifty = get_data('^NSEI')
 sensex = get_data('^BSESN')
 bull_pct, trend, ma20, ma50, rsi_now, atr = get_technical_chance('CL=F')
 now = datetime.now(IST).strftime('%I:%M %p, %d %b')
