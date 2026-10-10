# -*- coding: utf-8 -*-
import os, threading, time, requests, feedparser, pytz, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b'OK v9.8 PRO MAX')
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get('PORT', 10000))
 HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()
print('Step1 Health OK')

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = os.getenv('GROUP_ID', '-1004448478970')
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)
try:
    bot.delete_webhook(drop_pending_updates=True)
    print('Step2 Webhook deleted')
except:
    pass

IST = pytz.timezone('Asia/Kolkata')
ET = pytz.timezone('US/Eastern')
pinned_id = None
CACHE = {'news': {}, 'time': 0, 'us_open_sent': '', 'us_close_sent': ''}

def get_data_safe(sym):
    try:
        import yfinance as yf
        h = yf.Ticker(sym).history(period='5d')
        if h.empty: return None
        c = float(h['Close'].iloc[-1])
        p = float(h['Close'].iloc[-2]) if len(h) > 1 else c
        ch = ((c - p) / p * 100) if p != 0 else 0
        return {'price': c, 'change': ch}
    except: return None

def fetch_news_fast(query):
    try:
        q = query.replace(' ', '+')
        url = 'https://news.google.com/rss/search?q=' + q + '+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=10)
        feed = feedparser.parse(r.content)
        txt = ''; now_utc = datetime.now(pytz.utc); count = 0
        if feed.entries:
            for entry in feed.entries:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
                    if (now_utc - pub_time).total_seconds() > 86400: continue
                title = entry.title
                if len(title) < 15: continue
                title = title[:90].replace('<','').replace('>','').replace("'","")
                count += 1
                txt += str(count) + '. ' + title + '\n'
                if count >= 2: break
        if txt == '': return 'No major breaking in last 24h - Market stable\n'
        return txt
    except: return 'Market stable\n'

def refresh_cache():
    try:
        CACHE['news']['crude'] = fetch_news_fast('crude oil OPEC price today')
        CACHE['news']['nifty'] = fetch_news_fast('NSE Nifty Sensex FII DII today')
        CACHE['news']['world'] = fetch_news_fast('Trump Modi Putin Israel Iran war today')
        CACHE['news']['bulk'] = fetch_news_fast('NSE bulk block deal today')
        CACHE['news']['global'] = fetch_news_fast('US stock market Europe market today')
        CACHE['time'] = time.time()
    except: pass

threading.Thread(target=refresh_cache, daemon=True).start()

def make_hi_text():
    try:
        crude = get_data_safe('CL=F')
        nifty = get_data_safe('^NSEI')
        sensex = get_data_safe('^BSESN')
        vix = get_data_safe('^INDIAVIX')
        usdinr = get_data_safe('INR=X')
        gold = get_data_safe('GC=F')
        sp500 = get_data_safe('^GSPC')
        nasdaq = get_data_safe('^IXIC')
        dow = get_data_safe('^DJI')
        ftse = get_data_safe('^FTSE')
        dax = get_data_safe('^GDAXI')
        nikkei = get_data_safe('^N225')

        now = datetime.now(IST).strftime('%I:%M %p, %d %b')
        msg = '<b>🔥 PATIALA CRUDE LIVE 🔥</b>\n'
        msg += '<b>' + now + ' IST</b>\n'
        msg += '━━━━━━━━━━━━━━━━━━━━\n\n'

        if crude:
            rs_val = int(crude['price'] * usdinr['price']) if usdinr else 0
            col = '🟢' if crude['change'] >= 0 else '🔴'
            msg += '<b>🛢️ CRUDE OIL</b>\n'
            msg += col + ' <b>$' + str(round(crude['price'],2)) + ' (Rs ' + str(rs_val) + ')</b> <b>(' + str(round(crude['change'],2)) + '%)</b>\n\n'

        msg += '<b>🇮🇳 INDIA MARKET</b>\n'
        if nifty:
            col = '🟢' if nifty['change'] >= 0 else '🔴'
            msg += col + ' NIFTY 50: <b>' + str(round(nifty['price'],2)) + ' (' + str(round(nifty['change'],2)) + '%)</b>\n'
        if sensex:
            col = '🟢' if sensex['change'] >= 0 else '🔴'
            msg += col + ' SENSEX: <b>' + str(round(sensex['price'],2)) + ' (' + str(round(sensex['change'],2)) + '%)</b>\n'
        if gold:
            col = '🟢' if gold['change'] >= 0 else '🔴'
            msg += col + ' GOLD: <b>$' + str(round(gold['price'],2)) + '</b>\n'
        if vix:
            msg += '🔵 VIX: <b>' + str(round(vix['price'],2)) + '</b>\n'
        if usdinr:
            msg += '🔵 USD-INR: <b>' + str(round(usdinr['price'],2)) + '</b>\n'

        msg += '\n<b>🇺🇸 TOP 3 US MARKET</b>\n'
        if dow:
            col = '🟢' if dow['change'] >= 0 else '🔴'
            msg += col + ' <b>DOW JONES</b>: <b>' + str(round(dow['price'],2)) + ' (' + str(round(dow['change'],2)) + '%)</b>\n'
        if nasdaq:
            col = '🟢' if nasdaq['change'] >= 0 else '🔴'
            msg += col + ' <b>NASDAQ</b>: <b>' + str(round(nasdaq['price'],2)) + ' (' + str(round(nasdaq['change'],2)) + '%)</b>\n'
        if sp500:
            col = '🟢' if sp500['change'] >= 0 else '🔴'
            msg += col + ' <b>S&P 500</b>: <b>' + str(round(sp500['price'],2)) + ' (' + str(round(sp500['change'],2)) + '%)</b>\n'

        msg += '\n<b>🌍 GLOBAL</b>\n'
        if ftse:
            col = '🟢' if ftse['change'] >= 0 else '🔴'
            msg += col + ' FTSE 100: <b>' + str(round(ftse['price'],2)) + '</b>\n'
        if dax:
            col = '🟢' if dax['change'] >= 0 else '🔴'
            msg += col + ' DAX: <b>' + str(round(dax['price'],2)) + '</b>\n'
        if nikkei:
            col = '🟢' if nikkei['change'] >= 0 else '🔴'
            msg += col + ' NIKKEI: <b>' + str(round(nikkei['price'],2)) + '</b>\n'

        msg += '\n━━━━━━━━━━━━━━━━━━━━\n\n'
        msg += '<b>CRUDE IMPACT</b> (24H)\n' + CACHE['news'].get('crude','Loading...\n') + '\n'
        msg += '<b>NIFTY IMPACT</b> (24H)\n' + CACHE['news'].get('nifty','Loading...\n') + '\n'
        msg += '<b>WORLD + WAR</b> (24H)\n' + CACHE['news'].get('world','Loading...\n') + '\n'
        msg += '<b>GLOBAL NEWS</b> (24H)\n' + CACHE['news'].get('global','Loading...\n') + '\n'
        msg += '<b>BULK DEALS</b> (24H)\n' + CACHE['news'].get('bulk','Loading...\n') + '\n'
        msg += '━━━━━━━━━━━━━━━━━━━━\n'
        msg += 'Type <b>plan</b> | <b>/define PCR</b> for terms'
        return msg
    except Exception as e:
        return 'Bot LIVE - ' + str(e)

def get_us_alert_text(type_alert):
    try:
        dow = get_data_safe('^DJI')
        nasdaq = get_data_safe('^IXIC')
        sp500 = get_data_safe('^GSPC')
        if type_alert == 'open':
            msg = '<b>🇺🇸 US MARKET OPENED</b> 🟢\n'
            msg += datetime.now(IST).strftime('%I:%M %p IST') + '\n'
            msg += '━━━━━━━━━━━━━━━━━━━━\n'
            if dow: msg += 'DOW: <b>' + str(round(dow['price'],2)) + ' (' + str(round(dow['change'],2)) + '%)</b>\n'
            if nasdaq: msg += 'NASDAQ: <b>' + str(round(nasdaq['price'],2)) + ' (' + str(round(nasdaq['change'],2)) + '%)</b>\n'
            if sp500: msg
