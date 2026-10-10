# -*- coding: utf-8 -*-
# v14.4 CLEAN NO CUT
import os, threading, time, requests, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v14.4')
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self,*a):
        pass

def run_health():
    port = int(os.environ.get('PORT','10000'))
    HTTPServer(('0.0.0.0', port), H).serve_forever()

threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = os.getenv('GROUP_ID','-1004448478970')

if not BOT_TOKEN:
    print("TOKEN missing")
    while True:
        time.sleep(60)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)
CACHE = {'prices':{}, 'time':0}
LAST = set()

def get_prices():
    now = time.time()
    if now - CACHE['time'] < 120:
        if CACHE['prices']:
            return CACHE['prices']
    prices = {}
    try:
        import yfinance as yf
        for sym in ['CL=F','^NSEI','USO']:
            try:
                h = yf.Ticker(sym).history(period='5d')
                if h.empty:
                    continue
                c = float(h['Close'].iloc[-1])
                p2 = float(h['Close'].iloc[-2])
                ch = (c-p2)/p2*100 if p2 else 0
                v1 = float(h['Volume'].iloc[-1])
                v2 = float(h['Volume'].tail(5).mean())
                prices[sym] = {}
                prices[sym]['price'] = c
                prices[sym]['change'] = ch
                prices[sym]['vol'] = v1
                prices[sym]['vavg'] = v2
            except:
                continue
    except:
        pass
    if prices:
        CACHE['prices'] = prices
        CACHE['time'] = now
    return prices if prices else CACHE['prices']

def get_breaking():
    try:
        import feedparser
        url = 'https://news.google.com/rss/search?q=crude+oil+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=8)
        feed = feedparser.parse(r.content)
        p = get_prices()
        cr = 91.85
        if 'CL=F' in p:
            cr = p['CL=F']['price']
        for e in feed.entries:
            title = e.title.strip()
            link = e.link
            clean = title.split(' - ')[0]
            clean = clean.strip()
            if clean in LAST:
                continue
            low = clean.lower()
            if 'war' in low or 'attack' in low or 'cut' in low or 'crisis' in low:
                impact = 'BULLISH 90% UP'
            elif 'down' in low or 'fall' in low or 'supply' in low:
                impact = 'BEARISH 90% DOWN'
            else:
                impact = 'SIDEWAY 50%'
            LAST.add(clean)
            if len(LAST) > 100:
                LAST.clear()
                LAST.add(clean)
            src = title.split(' - ')[-1]
            msg1 = "🚨 <b>BREAKING</b> 🚨\n\n"
            msg2 = clean + "\n\n"
            msg3 = "IMPACT: " + impact + "\n"
            msg4 = "Crude: $" + str(round(cr,2)) + "\n"
            msg5 = "Source: " + src + "\n\n"
            msg6 = "<a href=\"" + link + "\">Full News - Click</a>"
            return msg1 + msg2 + msg3 + msg4 + msg5 + msg6
        return None
    except Exception as ex:
        print("news err", ex)
        return None

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip()=='news')
def news_h(m):
    txt = get_breaking()
    if txt:
        bot.send_message(m.chat.id, txt, disable_web_page_preview=False)
        if str(m.chat.id)!= GROUP_ID:
            try:
                bot.send_message(int(GROUP_ID), txt, disable_web_page_preview=False)
            except:
                pass
    else:
        bot.send_message(m.chat.id, "Abhi koi naya news nahi")

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','crude'])
def hi_h(m):
    p = get_prices()
    cr = p.get('CL=F',{'price':91.85,'change':0})
    ns = p.get('^NSEI',{'change':0})
    price = round(cr['price'],2)
    ch = round(cr['change'],2)
    nch = round(ns['change'],2)
    txt = "CRUDE STATUS\n"
    txt += "Crude: $" + str(price) + " (" + str(ch) + "%)\n"
    txt += "NSE: " + str(nch) + "%\nBuy on dip"
    bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['stock','fno'])
def stock_h(m):
    p = get_prices()
    cr = p.get('CL=F',{'price':91.85,'change':0})
    uso = p.get('USO',{'vol':0,'vavg':1})
    vol = uso['vol']
    vavg = uso['vavg']
    whale = "Shark: No big volume"
    try:
        pct = int(vol / vavg * 100) if vavg else 0
        if vol > vavg * 1.5:
            vml = round(vol/1e6,1)
            whale = "BIG SHARK LIVE " + str(vml) + "M (" + str(pct) + "%)"
    except:
        pass
    price = round(cr['price'],2)
    ch = round(cr['change'],2)
    txt = "F&O SCALP\n" + whale + "\n"
    txt += "Crude: $" + str(price) + " (" + str(ch) + "%)"
    bot.send_message(m.chat.id, txt)

@bot.message_handler(commands=['liveon','live'])
def liveon(m):
    p = get_prices()
    cr = p.get('CL=F',{'price':91.85})
    price = round(cr['price'],2)
    try:
        bot.send_message(int(GROUP_ID), "LIVE v14.4 $" + str(price))
    except:
        pass
    bot.reply_to(m, 'LIVE ON v14.4')

def updater():
    last = 0
    while True:
        time.sleep(60)
        t = time.time()
        if t - last >= 900:
            try:
                txt = get_breaking()
                if txt:
                    bot.send_message(int(GROUP_ID), txt, disable_web_page_preview=False)
            except Exception as ex:
                print("up err", ex)
            last = t

threading.Thread(target=updater, daemon=True).start()
print('Bot v14.4 LIVE')
while True:
    try:
        bot.infinity_polling(none_stop=True, timeout=90)
    except Exception as e:
        print("poll err", e)
        time.sleep(10)
