# -*- coding: utf-8 -*-
import os
import threading
import time
import requests
import feedparser
import pytz
import telebot
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v9.9 FIXED')
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, *a):
        pass

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
CACHE = {'news': {}, 'time': 0, 'us_open_sent': '', 'us_close_sent': ''}

def get_data_safe(sym):
    try:
        import yfinance as yf
        h = yf.Ticker(sym).history(period='5d')
        if h.empty:
            return None
        c = float(h['Close'].iloc[-1])
        p = float(h['Close'].iloc[-2]) if len(h) > 1 else c
        ch = 0
        if p!= 0:
            ch = (c - p) / p * 100
        return {'price': c, 'change': ch}
    except Exception:
        return None

def fetch_news_fast(query):
    try:
        q = query.replace(' ', '+')
        url = 'https://news.google.com/rss/search?q=' + q + '+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
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
                title = title[:90].replace('<','').replace('>','').replace("'","")
                count += 1
                txt += str(count) + '. ' + title + '\n'
                if count >= 2:
                    break
        if txt == '':
            return 'No major breaking in last 24h - Market stable\n'
        return txt
    except Exception:
        return 'Market stable\n'

def refresh_cache():
    try:
        CACHE['news']['crude'] = fetch_news_fast('crude oil OPEC price today')
        CACHE['news']['nifty'] = fetch_news_fast('NSE Nifty Sensex FII DII today')
        CACHE['news']['world'] = fetch_news_fast('Trump Modi Putin Israel Iran war today')
        CACHE['news']['bulk'] = fetch_news_fast('NSE bulk block deal today')
        CACHE['news']['global'] = fetch_news_fast('US stock market Europe market today')
        CACHE['time'] = time.time()
    except Exception:
        pass

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
        msg = '<b>PATIALA CRUDE LIVE</b>\n'
        msg += '<b>' + now + ' IST</b>\n'
        msg += '━━━━━━━━━━━━━━━━━━━━\n\n'

        if crude is not None:
            usd_price = usdinr['price'] if usdinr is not None else 0
            rs_val = int(crude['price'] * usd_price)
            col = '🟢' if crude['change'] >= 0 else '🔴'
            msg += '<b>CRUDE OIL</b>\n'
            msg += col + ' <b>$' + str(round(crude['price'],2)) + ' (Rs ' + str(rs_val) + ')</b> <b>(' + str(round(crude['change'],2)) + '%)</b>\n\n'

        msg += '<b>INDIA MARKET</b>\n'
        if nifty is not None:
            col = '🟢' if nifty['change'] >= 0 else '🔴'
            msg += col + ' NIFTY 50: <b>' + str(round(nifty['price'],2)) + ' (' + str(round(nifty['change'],2)) + '%)</b>\n'
        if sensex is not None:
            col = '🟢' if sensex['change'] >= 0 else '🔴'
            msg += col + ' SENSEX: <b>' + str(round(sensex['price'],2)) + '</b>\n'
        if gold is not None:
            col = '🟢' if gold['change'] >= 0 else '🔴'
            msg += col + ' GOLD: <b>$' + str(round(gold['price'],2)) + '</b>\n'
        if vix is not None:
            msg += '🔵 VIX: <b>' + str(round(vix['price'],2)) + '</b>\n'
        if usdinr is not None:
            msg += '🔵 USD-INR: <b>' + str(round(usdinr['price'],2)) + '</b>\n'

        msg += '\n<b>TOP 3 US MARKET</b>\n'
        if dow is not None:
            col = '🟢' if dow['change'] >= 0 else '🔴'
            msg += col + ' <b>DOW JONES</b>: <b>' + str(round(dow['price'],2)) + ' (' + str(round(dow['change'],2)) + '%)</b>\n'
        if nasdaq is not None:
            col = '🟢' if nasdaq['change'] >= 0 else '🔴'
            msg += col + ' <b>NASDAQ</b>: <b>' + str(round(nasdaq['price'],2)) + ' (' + str(round(nasdaq['change'],2)) + '%)</b>\n'
        if sp500 is not None:
            col = '🟢' if sp500['change'] >= 0 else '🔴'
            msg += col + ' <b>S&P 500</b>: <b>' + str(round(sp500['price'],2)) + ' (' + str(round(sp500['change'],2)) + '%)</b>\n'

        msg += '\n<b>GLOBAL</b>\n'
        if ftse is not None:
            col = '🟢' if ftse['change'] >= 0 else '🔴'
            msg += col + ' FTSE 100: <b>' + str(round(ftse['price'],2)) + '</b>\n'
        if dax is not None:
            col = '🟢' if dax['change'] >= 0 else '🔴'
            msg += col + ' DAX: <b>' + str(round(dax['price'],2)) + '</b>\n'
        if nikkei is not None:
            col = '🟢' if nikkei['change'] >= 0 else '🔴'
            msg += col + ' NIKKEI: <b>' + str(round(nikkei['price'],2)) + '</b>\n'

        msg += '\n━━━━━━━━━━━━━━━━━━━━\n\n'
        msg += '<b>CRUDE IMPACT</b> (24H)\n' + CACHE['news'].get('crude','Loading...\n') + '\n'
        msg += '<b>NIFTY IMPACT</b> (24H)\n' + CACHE['news'].get('nifty','Loading...\n') + '\n'
        msg += '<b>WORLD + WAR</b> (24H)\n' + CACHE['news'].get('world','Loading...\n') + '\n'
        msg += '<b>GLOBAL NEWS</b> (24H)\n' + CACHE['news'].get('global','Loading...\n') + '\n'
        msg += '<b>BULK DEALS</b> (24H)\n' + CACHE['news'].get('bulk','Loading...\n') + '\n'
        msg += '━━━━━━━━━━━━━━━━━━━━\n'
        msg += 'Type <b>plan</b> | <b>/define PCR</b>'
        return msg
    except Exception as e:
        return 'Bot LIVE - ' + str(e)

def get_us_alert_text(type_alert):
    try:
        dow = get_data_safe('^DJI')
        nasdaq = get_data_safe('^IXIC')
        sp500 = get_data_safe('^GSPC')
        now_str = datetime.now(IST).strftime('%I:%M %p IST')
        if type_alert == 'open':
            msg = '<b>US MARKET OPENED</b> 🟢\n'
            msg += now_str + '\n'
            msg += '━━━━━━━━━━━━━━━━━━━━\n'
            if dow is not None:
                msg += 'DOW: <b>' + str(round(dow['price'],2)) + ' (' + str(round(dow['change'],2)) + '%)</b>\n'
            if nasdaq is not None:
                msg += 'NASDAQ: <b>' + str(round(nasdaq['price'],2)) + ' (' + str(round(nasdaq['change'],2)) + '%)</b>\n'
            if sp500 is not None:
                msg += 'S&P 500: <b>' + str(round(sp500['price'],2)) + ' (' + str(round(sp500['change'],2)) + '%)</b>\n'
            msg += '\nTrend: '
            if sp500 is not None and sp500['change'] > 0.5:
                msg += '<b>BULLISH - Gap Up</b>'
            elif sp500 is not None and sp500['change'] < -0.5:
                msg += '<b>BEARISH - Gap Down</b>'
            else:
                msg += '<b>FLAT - Range</b>'
            msg += '\n\nKal NIFTY pe impact hoga!'
            return msg
        else:
            msg = '<b>US MARKET CLOSED</b> 🔵\n'
            msg += now_str + '\n'
            msg += '━━━━━━━━━━━━━━━━━━━━\n'
            if dow is not None:
                msg += 'DOW: <b>' + str(round(dow['price'],2)) + ' (' + str(round(dow['change'],2)) + '%)</b>\n'
            if nasdaq is not None:
                msg += 'NASDAQ: <b>' + str(round(nasdaq['price'],2)) + ' (' + str(round(nasdaq['change'],2)) + '%)</b>\n'
            if sp500 is not None:
                msg += 'S&P 500: <b>' + str(round(sp500['price'],2)) + ' (' + str(round(sp500['change'],2)) + '%)</b>\n'
            msg += '\nFinal: '
            if sp500 is not None and sp500['change'] > 0:
                msg += '<b>BULLISH Close - Kal NIFTY Gap Up chance</b>'
            else:
                msg += '<b>BEARISH Close - Kal Gap Down risk</b>'
            return msg
    except Exception as e:
        return 'US Market Update - ' + str(e)

GLOSSARY = {
 'orb': '<b>ORB = Opening Range Breakout</b>\nPehle 15 min (9:15-9:30) ka High/Low. Upar tode to LONG, neeche tode to SHORT.',
 'ema': '<b>EMA = Exponential Moving Average</b>\n20 EMA upar = short strong, 200 EMA upar = long bullish.',
 'pcr': '<b>PCR = Put Call Ratio</b>\nPCR 1.0+ = Bearish defensive, 0.8 neeche = Bullish. 1.15+ oversold bounce.',
 'fii': '<b>FII = Foreign Investors</b>\nVideshi funds beche to market neeche.',
 'dii': '<b>DII = Domestic Investors</b>\nIndian MF, LIC jo FII ko absorb karte.',
 'vix': '<b>VIX = Dar ka meter</b>\n15 upar = Dar, tez move. 12 neeche = Shant.',
 'sl': '<b>SL = Stop Loss</b>\nLoss limit, bina SL ke trade mat karo.',
 'dip': '<b>Dip Buy</b>\nUpar trend me neeche aake support pe hold to wapas LONG.',
 'breakdown': '<b>Breakdown</b>\nSupport todna, neeche jana.',
 'bulk': '<b>Bulk Deal</b>\nBade trader ka bada deal.',
}

def get_define_text(term):
    term = term.lower().strip()
    for key in GLOSSARY:
        if key in term:
            return GLOSSARY[key] + '\n\nType /define FII | /define EMA'
    return '<b>Term nahi mila: ' + term + '</b>\nAvailable: ORB, EMA, PCR, FII, DII, VIX, SL, DIP, BREAKDOWN, BULK\nEx: /define PCR'

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hii','hello','status','hey'])
def hi_handler(m):
    bot.send_message(m.chat.id, make_hi_text())

@bot.message_handler(func=lambda m: m.text and 'plan' in m.text.lower())
def plan_handler(m):
    nifty = get_data_safe('^NSEI')
    sp500 = get_data_safe('^GSPC')
    price = 22520
    if nifty is not None:
        price = int(nifty['price'])
    base = int(price / 10) * 10
    orb = base + 60
    long_entry = base + 80
    breakdown = base - 340
    sp_ch = '0%'
    if sp500 is not None:
        sp_ch = str(round(sp500['change'],2)) + '%'
    day_name = datetime.now(IST).strftime('%A').upper()
    plan = '<b>NIFTY 50 - TRADE PLAN</b>\n' + day_name + ' S&P: ' + sp_ch + '\n'
    plan += '━━━━━━━━━━━━━━━━━━━━\n\n'
    plan += '🟢 LONG: <b>' + str(orb) + ' upar = LONG ' + str(long_entry) + '</b>\n'
    plan += '🔴 SHORT: <b>' + str(breakdown) + ' tode = SHORT</b>\n\n'
    plan += 'Make-or-Break = <b>' + str(breakdown) + '</b>\n'
    plan += '\nType /define ORB'
    bot.send_message(m.chat.id, plan)

@bot.message_handler(commands=['define','explain','meaning'])
def define_handler(m):
    try:
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(m.chat.id, '<b>Use:</b> /define PCR\nTerms: ORB, EMA, PCR, FII, DII, VIX, SL, DIP, BREAKDOWN, BULK')
            return
        term = parts[1]
        bot.send_message(m.chat.id, get_define_text(term))
    except Exception as e:
        bot.send_message(m.chat.id, 'Error: ' + str(e))

@bot.message_handler(commands=['liveon','pinon'])
def liveon(m):
    global pinned_id
    try:
        msg = bot.send_message(int(GROUP_ID), make_hi_text())
        pinned_id = msg.message_id
        try:
            bot.pin_chat_message(int(GROUP_ID), pinned_id, disable_notification=True)
        except Exception:
            pass
        bot.reply_to(m, 'Live started v9.9 FIXED')
    except Exception as e:
        bot.reply_to(m, 'Error: ' + str(e))

def updater():
    global pinned_id
    while True:
        try:
            time.sleep(60)
            now_ist = datetime.now(IST)
            today_str = now_ist.strftime('%Y-%m-%d')
            time_str = now_ist.strftime('%H:%M')
            if time_str == '19:00' and now_ist.weekday() < 5:
                if CACHE['us_open_sent']!= today_str:
                    try:
                        txt = get_us_alert_text('open')
                        bot.send_message(int(GROUP_ID), txt)
                        CACHE['us_open_sent'] = today_str
                    except Exception:
                        pass
            if time_str == '01:30':
                if CACHE['us_close_sent']!= today_str:
                    try:
                        txt = get_us_alert_text('close')
                        bot.send_message(int(GROUP_ID), txt)
                        CACHE['us_close_sent'] = today_str
                    except Exception:
                        pass
            if int(time.time()) % 1800 < 60:
                refresh_cache()
                if pinned_id is not None:
                    try:
                        bot.edit_message_text(make_hi_text(), int(GROUP_ID), pinned_id)
                    except Exception:
                        pass
        except Exception:
            time.sleep(60)

threading.Thread(target=updater, daemon=True).start()
print('Bot polling started v9.9 FIXED LIVE')
while True:
    try:
        bot.infinity_polling(none_stop=True, timeout=90, skip_pending=True)
    except Exception as e:
        print('Polling error', e)
        time.sleep(10)
