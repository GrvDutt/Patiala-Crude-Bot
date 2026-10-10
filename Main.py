# -*- coding: utf-8 -*-
# CRUDE BOT v14.3 FINAL - FIXED LINE
import os, threading, time, requests, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v14.3 FINAL')
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self,*a):
        pass

def run_health():
    HTTPServer(('0.0.0.0', int(os.environ.get('PORT','10000'))), H).serve_forever()

threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = os.getenv('GROUP_ID','-1004448478970')

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN missing")
    while True:
        time.sleep(60)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)
CACHE = {'prices':{}, 'time':0}
LAST_TITLES = set()

def get_prices():
    try:
        if time.time()-CACHE['time']<120 and CACHE['prices']:
            return CACHE['prices']
    except:
        pass
    prices = {}
    try:
        import yfinance as yf
        for sym in ['CL=F','^NSEI','USO']:
            try:
                h = yf.Ticker(sym).history(period='5d')
                if h.empty:
                    continue
                c = float(h['Close'].iloc[-1])
                p2 = float(h['Close'].iloc[-2]) if len(h)>1 else c
                ch = (c-p2)/p2*100 if p2!=0 else 0.0
                v1 = float(h['Volume'].iloc[-1])
                v2 = float(h['Volume'].tail(5).mean())
                prices[sym] = {'price':c,'change':ch,'vol':v1,'vavg':v2}
            except Exception:
                continue
    except Exception:
        pass
    if prices:
        CACHE['prices'] = prices
        CACHE['time'] = time.time()
        return prices
    return CACHE['prices']

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
            clean_title = title.split(' - ')[0].strip()
            source = title.split(' - ')[-1] if ' - ' in title else 'News'
            if clean_title in LAST_TITLES:
                continue
            low = clean_title.lower()
            if 'war' in low or 'attack' in low or 'killed' in low or 'cut' in low or 'crisis' in low or 'sanction' in low:
                impact = 'BULLISH 90% UP ⬆️'
            elif 'down' in low or 'fall' in low or 'supply' in low or 'increase' in low or 'surplus' in low:
                impact = 'BEARISH 90% DOWN ⬇️'
            else:
                impact = 'SIDEWAY 50% 👀'
            LAST_TITLES.add(clean_title)
            if len(LAST_TITLES) > 100:
                LAST_TITLES.clear()
                LAST_TITLES.add(clean_title)
            msg = "🚨 <b>BREAKING - CRUDE IMPACT</b> 🚨\n\n⚠️ "+clean_title+"\n\n💥 IMPACT: "+impact+"\nCrude: $"+str(round(cr,2))+"\nSource: "+source+"\n\n🔗 <a href=\""+link+"\">Full News Padho - Click Here</a>"
            return msg
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
            except Exception:
                pass
    else:
        bot.send_message(m.chat.id, "Abhi koi naya news nahi 👀")

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hello','crude','hi crude'])
def hi_h(m):
    p = get_prices()
    cr = p.get('CL=F',{'price':91.85,'change':0.39})
    nse = p.get('^NSEI',{'change':0})
    # YAHI LINE FIX KI HAI - ab idhr error nahi ayega
    txt = "📊 CRUDE STATUS\nCrude: $" + str(round(cr['price'],2)) + " (" + str(round(cr['change'],2)) + "%)\nNSE: " + str(round(nse['change'],2)) + "%\n\n💡 View: Buy on dip"
    bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['stock','fno','f&o'])
def stock_h(m):
    p = get_prices()
    cr = p.get('CL=F',{'price':91.85,'change':0.39})
    uso = p.get('USO',{'vol':0,'vavg':1,'change':0})
    whale = "🦈 Shark: No big volume"
    try:
        vol_pct = int(uso['vol']/uso['vavg']*100) if uso['vavg']>0 else 0
        if uso['vol'] > uso['vavg
