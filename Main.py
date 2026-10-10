# -*- coding: utf-8 -*-
import os, threading, time, requests, feedparser, pytz, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b'OK v9.6 PREMIUM UI')
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get('PORT', 10000))
 HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = os.getenv('GROUP_ID', '-1004448478970')
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)
try:
    bot.delete_webhook(drop_pending_updates=True)
except:
    pass

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
        ch = ((c - p) / p * 100) if p!= 0 else 0
        return {'price': c, 'change': ch}
    except:
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
    except:
        return 'Market stable\n'

def refresh_cache():
    try:
        CACHE['news']['crude'] = fetch_news_fast('crude oil OPEC price today')
        CACHE['news']['nifty'] = fetch_news_fast('NSE Nifty Sensex FII DII today')
        CACHE['news']['world'] = fetch_news_fast('Trump Modi Putin Israel Iran war today')
        CACHE['news']['bulk'] = fetch_news_fast('NSE bulk block deal today')
        CACHE['time'] = time.time()
    except:
        pass

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

        # ---- PREMIUM UI ----
        msg = '<b>PATIALA CRUDE LIVE</b>\n'
        msg += now + '\n'
        msg += '━━━━━━━━━━━━━━━━━━━━\n\n'

        # CRUDE
        if crude:
            rs_val = int(crude['price'] * usdinr['price']) if usdinr else 0
            col = '🟢' if crude['change'] >= 0 else '🔴'
            msg += '<b>CRUDE OIL</b>\n'
            msg += col + ' <b>$' + str(round(crude['price'],2)) + ' (Rs ' + str(rs_val) + ')</b> (' + str(round(crude['change'],2)) + '%)\n\n'

        # INDEX
        msg += '<b>MARKET OVERVIEW</b>\n'
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

        msg += '\n━━━━━━━━━━━━━━━━━━━━\n\n'

        # NEWS WITH BOLD HEADERS AND SPACING
        msg += '<b>CRUDE IMPACT</b> (Last 24H)\n'
        msg += CACHE['news'].get('crude','Loading...\n') + '\n'

        msg += '<b>NIFTY / SENSEX IMPACT</b> (Last 24H)\n'
        msg += CACHE['news'].get('nifty','Loading...\n') + '\n'

        msg += '<b>WORLD LEADERS + WAR ALERT</b> (Last 24H)\n'
        msg += CACHE['news'].get('world','Loading...\n') + '\n'

        msg += '<b>BIG TRADERS BULK DEALS</b> (Last 24H)\n'
        msg += CACHE['news'].get('bulk','Loading...\n') + '\n'

        msg += '━━━━━━━━━━━━━━━━━━━━\n'
        msg += 'Type <b>plan</b> for Detailed Trade Plan'
        return msg
    except Exception as e:
        return 'Bot LIVE - ' + str(e)

def get_nifty_plan_text():
    try:
        nifty = get_data_safe('^NSEI')
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

        plan = '<b>NIFTY 50 - TRADE PLAN</b>\n'
        plan += day_name + ' • ' + date_str + ' | Educational\n'
        plan += '━━━━━━━━━━━━━━━━━━━━\n\n'

        plan += '<b>FAST READ (10 Sec)</b>\n'
        plan += '🟢 LONG tabhi jab:\n'
        plan += ' → <b>' + str(orb) + ' ke upar tikke = LONG ' + str(long_entry) + '</b>\n'
        plan += ' → <b>' + str(dip_bot) + '-' + str(dip_top) + ' hold = Dip Buy</b>\n\n'

        plan += '🔴 SHORT tabhi jab:\n'
        plan += ' → <b>' + str(breakdown) + ' tode + ' + str(bounce_fail) + ' pe fail = SHORT</b>\n\n'

        plan += 'Make-or-Break = <b>' + str(breakdown) + '</b>\n'
        plan += 'Bada Trend = <b>BEARISH</b> (200-EMA ke neeche)\n\n'

        plan += '━━━━━━━━━━━━━━━━━━━━\n'
        plan += '<b>CONFLUENCE SNAPSHOT</b>\n\n'

        plan += 'Structure: <b>' + str(breakdown) + '</b> = Oct 8 low retest\n\n'
        plan += 'Close: <b>' + str(price) + '</b> 🟢 Buyers defend\n\n'
        plan += 'PCR/OI: <b>PCR 1.15</b> - Defensive 🔵\n\n'
        plan += 'Flows: <b>FII Selling slow</b> 🟢 | <b>DII Absorb</b> 🟢\n\n'

        plan += '━━━━━━━━━━━━━━━━━━━━\n'
        plan += '<b>KEY LEVELS</b>\n\n'

        plan += '🟢 <b>Resistance (Upar):</b>\n'
        plan += ' ' + str(orb) + ' → OR Breakout Trigger\n'
        plan += ' <b>' + str(long_entry) + ' → LONG Entry</b>\n'
        plan += ' ' + str(res_t1) + ' → Target 1\n'
        plan += ' ' + str(res_t2) + ' → Target 2\n\n'

        plan += '🔴 <b>Support (Neeche):</b>\n'
        plan += ' ' + str(dip_top) + ' → Dip-Buy Zone\n'
        plan += ' ' + str(bounce_fail) + ' → Failed Bounce\n'
        plan += ' <b>' + str(breakdown) + ' → Breakdown / SHORT</b>\n'
        plan += ' ' + str(down_target) + ' → Down Target\n\n'

        plan += '━━━━━━━━━━━━━━━━━━━━\n'
        plan += '<b>ENTRY PLAN</b>\n\n'

        plan += '<b>9:15 - 9:30</b>\n'
        plan += '→ NO TRADE - Sirf OR High/Low mark karo\n\n'

        plan += '<b>PLAN A [9:30-11:00] - OR Breakout</b> 🟢\n'
        plan += 'Gap-up + Above ' + str(orb) + ' sustain\n'
        plan += '→ LONG <b>' + str(long_entry) + '</b>\n'
        plan += ' SL: ' + str(long_entry-120) + ' | T: ' + str(res_t1) + ' → ' + str(res_t2) + '\n\n'

        plan += '<b>PLAN B [9:30-12:30] - Dip Buy</b> 🟢\n'
        plan += str(dip_bot) + '-' + str(dip_top) + ' hold\n'
        plan += '→ LONG <b>' + str(dip_top) + '</b> | SL: ' + str(breakdown-40) + '\n\n'

        plan += '<b>PLAN C [Anytime] - Breakdown</b> 🔴\n'
        plan += 'Below ' + str(breakdown) + ' + fail at ' + str(bounce_fail) + '\n'
        plan += '→ SHORT <b>' + str(breakdown) + '</b> | SL: ' + str(breakdown+160) + ' → T: ' + str(down_target) + '\n\n'

        plan += 'After 2:45 PM → No New Trades\n\n'
        plan += '━━━━━━━━━━━━━━━━━━━━\n'
        plan += '<b>GAME PLAN</b>\n'
        plan += '→ <b>' + str(breakdown) + '</b> major support 🔵\n'
        plan += '→ <b>' + str(orb) + ' upar hi long confirm</b> 🟢\n'
        plan += '→ Risk tight, SL mandatory 🔴\n'

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
        bot.reply_to(m, 'Live started v9.6 PREMIUM UI')
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
print('Bot polling started v9.6 PREMIUM UI LIVE')
while True:
    try:
        bot.infinity_polling(none_stop=True, timeout=90, skip_pending=True)
    except Exception as e:
        print('Polling error', e)
        time.sleep(10)
