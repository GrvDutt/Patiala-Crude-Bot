# -*- coding: utf-8 -*-
# CRUDE BOT v12.6 - NEVER EXIT - FINAL
import os, threading, time, requests, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b'OK v12.6 LIVE')
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
    def log_message(self,*a): pass

def run_health():
    port=int(os.environ.get('PORT','10000'))
    HTTPServer(('0.0.0.0', port), H).serve_forever()

threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN=os.getenv('BOT_TOKEN')
GROUP_ID=os.getenv('GROUP_ID','-1004448478970')

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN missing in Render Env")
    while True:
        time.sleep(60)

bot=telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)

CACHE={'prices':{}, 'time':0}
LAST_BIG=set()
LAST_BIG_BUYER=0

def get_prices():
    if time.time()-CACHE['time']<120 and CACHE['prices']:
        return CACHE['prices']
    prices={}
    try:
        import yfinance as yf
        h=yf.Ticker('CL=F').history(period='5d')
        if not h.empty:
            c=float(h['Close'].iloc[-1])
            p2=float(h['Close'].iloc[-2]) if len(h)>1 else c
            ch=(c-p2)/p2*100 if p2 else 0
            prices['CL=F']={'price':c,'change':ch,'vol':1,'vavg':1}
    except:
        pass
    if prices:
        CACHE['prices']=prices; CACHE['time']=time.time()
    return CACHE['prices']

@bot.message_handler(func=lambda m: True)
def all_h(m):
    try:
        txt=m.text.lower() if m.text else ""
        if '?' in txt or 'command' in txt or 'help' in txt:
            bot.reply_to(m, "BOT v12.6 LIVE\n? help\nhi crude\nnews\nstock\n/liveon")
            return
        if 'hi' in txt or 'crude' in txt:
            p=get_prices(); cr=p.get('CL=F',{'price':91.85})['price']
            bot.reply_to(m, "CRUDE $"+str(round(cr,2)))
            return
        if 'news' in txt:
            bot.reply_to(m, "BREAKING check group")
            try:
                import feedparser
                url='https://news.google.com/rss/search?q=crude+oil+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
                r=requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=5)
                feed=feedparser.parse(r.content)
                if feed.entries:
                    bot.send_message(int(GROUP_ID), "BREAKING\n"+feed.entries[0].title)
            except:
                pass
            return
        if 'stock' in txt or 'fno' in txt:
            p=get_prices(); cr=p.get('CL=F',{'price':91.85})['price']
            bot.reply_to(m, "FNO Crude $"+str(round(cr,2)))
            return
        if txt.startswith('/liveon') or txt.startswith('liveon'):
            p=get_prices(); cr=p.get('CL=F',{'price':91.85})['price']
            bot.send_message(int(GROUP_ID), "LIVE v12.6 Crude $"+str(round(cr,2)))
            bot.reply_to(m, 'LIVE ON v12.6')
    except Exception as e:
        print("Handler error", e)

print('Bot v12.6 STARTING - Will never exit')
while True:
    try:
        bot.infinity_polling(none_stop=True, timeout=60, long_polling_timeout=60)
    except Exception as e:
        print("Polling crash, retry in 10s:", e)
        time.sleep(10)
