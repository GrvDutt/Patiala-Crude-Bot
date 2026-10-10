import os, threading, json
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v8.2 NO EMOJI FIXED")
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
    atr = float((df['High'] - df['Low']).rolling(14).mean().iloc[-1])
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
     trend = 'BULLISH'
    elif bullish_pct <= 40:
     trend = 'BEARISH'
    else:
     trend = 'STABLE'
    return bullish_pct, trend, ma20, ma50, rsi_now, atr
  except Exception as e:
    print('Tech error', e)
    return 50, 'STABLE', 0, 0, 50, 0

def impact(head):
 hl = head.lower()
 red_words = ['fall','down','drops','slump','plunge','decline','weak','surplus','build','oversupply','recession']
 green_words = ['cut','war','tension','attack','strike','disrupt','blast','embargo','sanction','draw']
 if any(x in hl for x in red_words):
  return 'RED BEARISH'
 if any(x in hl for x in green_words):
  return 'GREEN BULLISH'
 return 'BLUE NEUTRAL'

def get_news():
  try:
    feed = feedparser.parse('https://news.google.com/rss/search?q=crude+oil+OPEC&hl=en-IN&gl=IN&ceid=IN:en')
    if feed.entries:
      txt = ''
      for i in range(3):
        h = feed.entries[i].title[:70].replace('<','').replace('>','')
        imp = impact(h)
        txt += str(i+1) + '. ' + h + ' - ' + imp + '\n'
      return txt
  except:
   pass
  return '1. OPEC supply in focus - NEUTRAL\n2. US inventory awaited - NEUTRAL\n3. Crude outlook stable - NEUTRAL\n'

def get_nifty_plan_text():
  nifty_data = get_data('^NSEI')
  if nifty_data:
   base = int(nifty_data['price'] / 50) * 50
   res1 = base + 80
   res2 = base + 150
   res3 = base + 300
   sup1 = base - 100
   sup2 = base - 200
   sup3 = base - 350
   make_break = sup2
  else:
   res1 = 22580
   res2 = 22600
   res3 = 22775
   sup1 = 22400
   sup2 = 22220
   sup3 = 22000
   make_break = 22180
  lines = []
  lines.append('<b>NIFTY 50 - TRADE PLAN</b>')
  lines.append('<b>' + datetime.now(IST).strftime('%A %d %b %Y') + '</b> | Educational')
  lines.append('--------------------------')
  lines.append('FAST READ')
  lines.append('LONG: ' + str(res1) + ' upar = LONG ' + str(res2))
  lines.append('SHORT: ' + str(sup2) + ' tode + ' + str(sup2+40) + ' fail')
  lines.append('Make-or-Break = ' + str(make_break))
  lines.append('--------------------------')
  lines.append('LEVELS Res: ' + str(res1) + ' -> ' + str(res2) + ' -> ' + str(res3))
  lines.append('Sup: ' + str(sup1) + ' -> ' + str(sup2) + ' -> ' + str(sup3))
  lines.append('--------------------------')
  lines.append('PLAN A LONG ' + str(res2) + ' SL ' + str(res2-120) + ' TGT ' + str(res3))
  lines.append('PLAN B LONG ' + str(sup1) + ' SL ' + str(sup1-260) + ' TGT ' + str(res1))
  lines.append('PLAN C SHORT ' + str(make_break) + ' SL ' + str(make_break+160) + ' TGT ' + str(sup3))
  return '\n'.join(lines)

def make_hi_text():
 inr = get_inr()
 crude = get_data('CL=F')
 nifty = get_data('^NSEI')
 sensex = get_data('^BSESN')
 gold = get_data('GC=F')
 bull_pct, trend, ma20, ma50, rsi_now, atr = get_technical_chance('CL=F')
 now = datetime.now(IST).strftime('%I:%M %p, %d %b')
 news = get_news()
 msg = '<b>PATIALA CRUDE LIVE - ' + now + '</b>\n\n'
 if crude:
  label = '$' + str(round(crude['price'],2)) + ' (Rs ' + str(int(crude['price']*inr)) + ')'
  msg += 'CRUDE OIL\n'
  msg += color_fmt(crude['change'], label) + '\n'
  msg += 'Trend: ' + trend + ' [' + str(bull_pct) + '%] | RSI ' + str(int(rsi_now)) + '\n'
  msg += 'MA20: ' + str(round(ma20,2)) + ' | MA50: ' + str(round(ma50,2)) + ' | ATR: ' + str(round(atr,2)) + '\n\n'
 if nifty:
  msg += 'NIFTY: ' + color_fmt(nifty['change'], str(round(nifty['price'],2))) + '\n'
 if sensex:
  msg += 'SENSEX: ' + color_fmt(sensex['change'], str(round(sensex['price'],2))) + '\n'
 if gold:
  msg += 'GOLD: ' + color_fmt(gold['change'], '$' + str(round(gold['price'],1))) + '\n'
 msg += '\nNEWS IMPACT\n' + news + '\n'
 msg += 'Commands: plan | /alert crude 92 | /alerts'
 return msg

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hii','hello','status'])
def hi_handler(m):
 bot.send_message(m.chat.id, make_hi_text())

@bot.message_handler(func=lambda m: m.text and 'plan' in m.text.lower() and not m.text.startswith('/'))
def plan_handler(m):
 bot.send_message(m.chat.id, get_nifty_plan_text())

@bot.message_handler(commands=['alert'])
def alert_handler(m):
 try:
  parts = m.text.split()
  if len(parts) < 3:
   bot.reply_to(m, 'Use: /alert crude 92')
   return
  sym = parts[1].lower()
  price = float(parts[2])
  key = str(m.chat.id) + '_' + sym
  alerts[key] = {'chat': m.chat.id, 'sym': sym, 'price': price}
  save_alerts()
  bot.reply_to(m, 'Alert set: ' + sym.upper() + ' at ' + str(price))
 except Exception as e:
  bot.reply_to(m, 'Error: ' + str(e))

@bot.message_handler(commands=['alerts'])
def list_alerts(m):
  txt = 'Alerts:\n'
  found = False
  for k,v in alerts.items():
   if str(v['chat']) == str(m.chat.id):
    txt += '- ' + v['sym'].upper() + ' at ' + str(v['price']) + '\n'
    found = True
  if not found:
   txt = 'No alerts. Use /alert crude 92'
  bot.send_message(m.chat.id, txt)

@bot.message_handler(commands=['liveon','pinon'])
def liveon(m):
 global pinned_id
 msg = bot.send_message(GROUP_ID, make_hi_text())
 pinned_id = msg.message_id
 try:
  bot.pin_chat_message(GROUP_ID, pinned_id, disable_notification=True)
 except:
  pass

def updater():
 global pinned_id
 while True:
  try:
   time.sleep(900)
   print('15 min update tick')
   if pinned_id:
    try:
     bot.edit_message_text(make_hi_text(), GROUP_ID, pinned_id)
    except Exception as e:
     print('Edit error', e)
  except Exception as e:
   print('Updater error', e)
   time.sleep(60)

threading.Thread(target=updater, daemon=True).start()

while True:
    try:
        print('Bot polling started v8.2 NO EMOJI - LIVE')
        bot.infinity_polling(none_stop=True, timeout=90, skip_pending=True)
    except Exception as e:
        print('Polling error', e)
        time.sleep(10)
