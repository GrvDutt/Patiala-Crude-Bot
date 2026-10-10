# -*- coding: utf-8 -*-
import os, threading, time, requests, feedparser, pytz, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b'OK v9.7 GLOBAL FULL')
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
        print('data err', e)
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
                title = title[:90].replace('<','').replace('>','').replace("'","")
                count += 1
                txt += str(count) + '. ' + title + '\n'
                if count >= 2:
                    break
        if txt == '':
            return 'No major breaking in last 24h - Market stable\n'
        return txt
    except Exception as e:
        print('News error', e)
        return 'Market stable\n'

def refresh_cache():
    try:
        print('Refreshing cache...')
        CACHE['news']['crude'] = fetch_news_fast('crude oil OPEC price today')
        CACHE['news']['nifty'] = fetch_news_fast('NSE Nifty Sensex FII DII today')
        CACHE['news']['world'] = fetch_news_fast('Trump Modi Putin Israel Iran war today')
        CACHE['news']['bulk'] = fetch_news_fast('NSE bulk block deal today')
        CACHE['news']['global'] = fetch_news_fast('US stock market Europe market today')
        CACHE['time'] = time.time()
        print('Cache OK')
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
        sp500 = get_data_safe('^GSPC')
        nasdaq = get_data_safe('^IXIC')
        dow = get_data_safe('^DJI')
        ftse = get_data_safe('^FTSE')
        dax = get_data_safe('^GDAXI')
        nikkei = get_data_safe('^N225')

        now = datetime.now(IST).strftime('%I:%M %p, %d %b')
        msg = '<b>PATIALA CRUDE LIVE</b>\n'
        msg += now + '\n'
        msg += '━━━━━━━━━━━━━━━━━━━━\n\n'

        if crude:
            rs_val = int(crude['price'] * usdinr['price']) if usdinr else 0
            col = '🟢' if crude['change'] >= 0 else '🔴'
            msg += '<b>CRUDE OIL</b>\n'
            msg += col + ' <b>$' + str(round(crude['price'],2)) + ' (Rs ' + str(rs_val) + ')</b> (' + str(round(crude['change'],2)) + '%)\n\n'

        msg += '<b>INDIA MARKET</b>\n'
        if nifty:
            col = '🟢' if nifty['change'] >= 0 else '🔴'
            msg += col + ' NIFTY 50: <b>' + str(round(nifty['price'],2)) + '</b> (' + str(round(nifty['change'],2)) + '%)\n'
        if sensex:
            col = '🟢' if sensex['change'] >= 0 else '🔴'
            msg += col + ' SENSEX: <b>' + str(round(sensex['price'],2)) + '</b>\n'
        if gold:
            col = '🟢' if gold['change'] >= 0 else '🔴'
            msg += col + ' GOLD: <b>$' + str(round(gold['price'],2)) + '</b>\n'
        if vix:
            msg += '🔵 VIX: <b>' + str(round(vix['price'],2)) + '</b>\n'
        if usdinr:
            msg += '🔵 USD-INR: <b>' + str(round(usdinr['price'],2)) + '</b>\n'

        msg += '\n<b>GLOBAL MARKET</b>\n'
        msg += '<b>USA</b>:\n'
        if sp500:
            col = '🟢' if sp500['change'] >= 0 else '🔴'
            msg += col + ' S&P 500: <b>' + str(round(sp500['price'],2)) + '</b> (' + str(round(sp500['change'],2)) + '%)\n'
        if nasdaq:
            col = '🟢' if nasdaq['change'] >= 0 else '🔴'
            msg += col + ' NASDAQ: <b>' + str(round(nasdaq['price'],2)) + '</b> (' + str(round(nasdaq['change'],2)) + '%)\n'
        if dow:
            col = '🟢' if dow['change'] >= 0 else '🔴'
            msg += col + ' DOW: <b>' + str(round(dow['price'],2)) + '</b> (' + str(round(dow['change'],2)) + '%)\n'

        msg += '<b>EUROPE</b>:\n'
        if ftse:
            col = '🟢' if ftse['change'] >= 0 else '🔴'
            msg += col + ' FTSE 100: <b>' + str(round(ftse['price'],2)) + '</b> (' + str(round(ftse['change'],2)) + '%)\n'
        if dax:
            col = '🟢' if dax['change'] >= 0 else '🔴'
            msg += col + ' DAX: <b>' + str(round(dax['price'],2)) + '</b> (' + str(round(dax['change'],2)) + '%)\n'

        msg += '<b>ASIA</b>:\n'
        if nikkei:
            col = '🟢' if nikkei['change'] >= 0 else '🔴'
            msg += col + ' NIKKEI: <b>' + str(round(nikkei['price'],2)) + '</b> (' + str(round(nikkei['change'],2)) + '%)\n'

        msg += '\n━━━━━━━━━━━━━━━━━━━━\n\n'
        msg += '<b>CRUDE IMPACT</b> (24H)\n' + CACHE['news'].get('crude','Loading...\n') + '\n'
        msg += '<b>NIFTY IMPACT</b> (24H)\n' + CACHE['news'].get('nifty','Loading...\n') + '\n'
        msg += '<b>WORLD + WAR</b> (24H)\n' + CACHE['news'].get('world','Loading...\n') + '\n'
        msg += '<b>GLOBAL NEWS</b> (24H)\n' + CACHE['news'].get('global','Loading...\n') + '\n'
        msg += '<b>BULK DEALS</b> (24H)\n' + CACHE['news'].get('bulk','Loading...\n') + '\n'
        msg += '━━━━━━━━━━━━━━━━━━━━\n'
        msg += 'Type <b>plan</b> for Trade Plan'
        return msg
    except Exception as e:
        return 'Bot LIVE - ' + str(e)

def get_nifty_plan_text():
    try:
        nifty = get_data_safe('^NSEI')
        sp500 = get_data_safe('^GSPC')
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
        sp_ch = str(round(sp500['change'],2)) + '%' if sp500 else '0%'

        plan = '<b>NIFTY 50 - TRADE PLAN</b>\n'
        plan += day_name + ' • ' + date_str + ' | Edu\n'
        plan += 'S&P 500: ' + sp_ch + '\n'
        plan += '━━━━━━━━━━━━━━━━━━━━\n\n'
        plan += '<b>FAST READ</b>\n'
        plan += '🟢 LONG: <b>' + str(orb) + ' upar = LONG ' + str(long_entry) + '</b>\n'
        plan += '🔴 SHORT: <b>' + str(breakdown) + ' tode = SHORT</b>\n\n'
        plan += 'Make-or-Break = <b>' + str(breakdown) + '</b> 🔵\n\n'
        plan += '━━━━━━━━━━━━━━━━━━━━\n'
        plan += '<b>KEY LEVELS</b>\n\n'
        plan += '🟢 Resistance: ' + str(orb) + ' -> <b>' + str(long_entry) + '</b> -> ' + str(res_t1) + '\n\n'
        plan += '🔴 Support: ' + str(dip_top) + ' -> <b>' + str(breakdown) + '</b> -> ' + str(down_target) + '\n\n'
        plan += '━━━━━━━━━━━━━━━━━━━━\n'
        plan += '<b>ENTRY PLAN</b>\n\n'
        plan += '<b>PLAN A OR Breakout</b> 🟢\nAbove ' + str(orb) + ' = LONG ' + str(long_entry) + ' SL ' + str(long_entry-120) + '\n\n'
        plan += '<b>PLAN B Dip Buy</b> 🟢\n' + str(dip_bot) + '-' + str(dip_top) + ' hold = LONG\n\n'
        plan += '<b>PLAN C Breakdown</b> 🔴\nBelow ' + str(breakdown) + ' = SHORT\n\n'
        plan += 'Risk tight, SL mandatory 🔴\n'
        return plan
    except Exception as e:
        return 'Plan error: ' + str(e)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hii','hello','status','hey'])
def hi_handler(m):
    bot.send_message(m.chat.id, make_hi_text())

@bot.message_handler(func=lambda m: m.text and 'plan' in m.text.lower())
def plan_handler(m):
    bot.send_message(m.chat.id, get_nifty_plan_text())

@bot.message_handler(commands=['liveon','pinon'])
def liveon(m):
    global pinned_id
    try:
        msg = bot.send_message(int(GROUP_ID), make_hi_text())
        pinned_id = msg.message_id
        try:
            bot.pin_chat_message(int(GROUP_ID), pinned_id, disable_notification=True)
        except:
            pass
        bot.reply_to(m, 'Live started v9.7 GLOBAL FULL')
    except Exception as e:
        bot.reply_to(m, 'Error: ' + str(e))

def updater():
    global pinned_id
    while True:
        try:
            time.sleep(1800)
            refresh_cache()
            if pinned_id:
                try:
                    bot.edit_message_text(make_hi_text(), int(GROUP_ID), pinned_id)
                except:
                    pass
        except:
            time.sleep(60)

threading.Thread(target=updater, daemon=True).start()
print('Bot polling started v9.7 GLOBAL FULL LIVE')
while True:
    try:
        bot.infinity_polling(none_stop=True, timeout=90, skip_pending=True)
    except Exception as e:
        print('Polling error', e)
        time.sleep(10)
