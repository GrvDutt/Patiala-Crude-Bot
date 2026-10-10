import os, threading, time, requests, feedparser, pytz, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b'OK v9.3 ULTIMATE FINAL')
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get('PORT', 10000))
 print('Health on', port)
 HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()
print('Step1 Health OK')

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = os.getenv('GROUP_ID', '-1004448478970')
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)
try:
    bot.delete_webhook(drop_pending_updates=True)
    print('Step2 Webhook deleted')
except Exception as e:
    print('Webhook err', e)

IST = pytz.timezone('Asia/Kolkata')
pinned_id = None
CACHE = {'news': {}, 'time': 0}

def get_data_safe(sym):
    try:
        import yfinance as yf
        h = yf.Ticker(sym).history(period='5d')
        if h.empty:
            return None
        c = float(h['Close'].iloc[-1])
        p = float(h['Close'].iloc[-2]) if len(h) > 1 else c
        ch = ((c - p) / p * 100) if p != 0 else 0
        return {'price': c, 'change': ch}
    except Exception as e:
        print('data err', sym, e)
        return None

def fetch_news_fast(query):
    try:
        q = query.replace(' ', '+')
        url = 'https://news.google.com/rss/search?q=' + q + '+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        feed = feedparser.parse(r.content)
        txt = ''
        now_utc = datetime.now(pytz.utc)
        count = 0
        if feed.entries:
            for entry in feed.entries:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
                    if (now_utc - pub_time).total_seconds() > 86400:
                        continue
                title = entry.title
                if len(title) < 15:
                    continue
                if 'SCO summit' in title:
                    continue
                title = title[:90].replace('<','').replace('>','')
                count += 1
                txt += str(count) + '. ' + title + '\n'
                if count >= 2:
                    break
        if txt == '':
            return 'No major breaking in last 24h - Market stable\n'
        return txt
    except Exception as e:
        print('News error', query, e)
        return 'Market stable - No major news\n'

def refresh_cache():
    try:
        print('Refreshing 24h cache...')
        CACHE['news']['crude'] = fetch_news_fast('crude oil OPEC price today')
        CACHE['news']['nifty'] = fetch_news_fast('NSE Nifty Sensex FII DII today')
        CACHE['news']['world'] = fetch_news_fast('Trump Modi Putin Israel Iran war today')
        CACHE['news']['bulk'] = fetch_news_fast('NSE bulk block deal today')
        CACHE['time'] = time.time()
        print('24h Cache OK')
    except Exception as e:
        print('Cache error', e)

threading.Thread(target=refresh_cache, daemon=True).start()

def make_hi_text():
    try:
        if time.time() - CACHE['time'] > 1800:
            threading.Thread(target=refresh_cache, daemon=True).start()
        crude = get_data_safe('CL=F')
        nifty = get_data_safe('^NSEI')
        sensex = get_data_safe('^BSESN')
        vix = get_data_safe('^INDIAVIX')
        usdinr = get_data_safe('INR=X')
        gold = get_data_safe('GC=F')
        now = datetime.now(IST).strftime('%I:%M %p, %d %b')
        msg = '📌 PATIALA CRUDE LIVE - ' + now + '\n\n'
        if crude:
            rs_val = int(crude['price'] * usdinr['price']) if usdinr else 0
            col = '🟢' if crude['change'] >= 0 else '🔴'
            msg += '🛢️ CRUDE OIL\n' + col + ' $' + str(round(crude['price'],2)) + ' (Rs ' + str(rs_val) + ') (' + str(round(crude['change'],2)) + '%)\n\n'
        if nifty:
            col = '🟢' if nifty['change'] >= 0 else '🔴'
            msg += 'NIFTY: ' + col + ' ' + str(round(nifty['price'],2)) + ' (' + str(round(nifty['change'],2)) + '%)\n'
        if sensex:
            col = '🟢' if sensex['change'] >= 0 else '🔴'
            msg += 'SENSEX: ' + col + ' ' + str(round(sensex['price'],2)) + '\n'
        if gold:
            col = '🟢' if gold['change'] >= 0 else '🔴'
            msg += 'GOLD: ' + col + ' $' + str(round(gold['price'],2)) + '\n'
        if vix:
            msg += 'VIX: ' + str(round(vix['price'],2)) + ' | '
        if usdinr:
            msg += 'USD-INR: ' + str(round(usdinr['price'],2)) + '\n'
        msg += '\n━━━━━━━━━━━━━━\n'
        msg += '🛢️ CRUDE (Last 24H)\n' + CACHE['news'].get('crude','Loading...\n') + '\n'
        msg += '📈 NIFTY IMPACT (Last 24H)\n' + CACHE['news'].get('nifty','Loading...\n') + '\n'
        msg += '🌍 WORLD + WAR (Last 24H)\n' + CACHE['news'].get('world','Loading...\n') + '\n'
        msg += '💰 BULK DEALS (Last 24H)\n' + CACHE['news'].get('bulk','Loading...\n') + '\n'
        msg += '💡 Type plan for Detailed Trade Plan'
        return msg
    except Exception as e:
        print('make_hi err', e)
        return 'Bot LIVE - ' + str(e)

def get_nifty_plan_text():
    try:
        nifty = get_data_safe('^NSEI')
        nasdaq = get_data_safe('^IXIC')
        brent = get_data_safe('BZ=F')
        price = int(nifty['price']) if nifty else 22520
        base = int(price / 10) * 10
        orb = base + 60
        long_entry = base + 80
        dip_top = base - 70
        dip_bot = base - 120
        breakdown = base - 340
        bounce_fail = breakdown + 40
        down_target = base - 520
        res_t1 = long_entry + 175
        res_t2 = long_entry + 350
        day_name = datetime.now(IST).strftime('%A').upper()
        date_str = datetime.now(IST).strftime('%d %b %Y')
        nasdaq_ch = str(round(nasdaq['change'],2)) + '%' if nasdaq else '+0.85%'
        brent_ch = str(round(brent['change'],2)) + '%' if brent else '-1.2%'
        plan = '📌 NIFTY 50 - TRADE PLAN\n'
        plan += day_name + ' • ' + date_str + ' | Educational\n'
        plan += '━━━━━━━━━━━━━━━━━━━━\n\n'
        plan += '⚡ FAST READ (10 Sec)\n'
        plan += '🐂 LONG tabhi jab:\n'
        plan += ' → ' + str(orb) + ' ke upar tikke = LONG ' + str(long_entry) + '\n'
        plan += ' → ' + str(dip_bot) + '-' + str(dip_top) + ' hold kare = Dip Buy\n\n'
        plan += '🐻 SHORT tabhi
