# -*- coding: utf-8 -*-
# CRUDE BOT v14.1 FINAL - 15 MIN + LINK + NO REPEAT
import os, threading, time, requests, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b'OK v14.1 FINAL')
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
    def log_message(self,*a): pass

def run_health():
    HTTPServer(('0.0.0.0', int(os.environ.get('PORT','10000'))), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN=os.getenv('BOT_TOKEN')
GROUP_ID=os.getenv('GROUP_ID','-1004448478970')

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN missing in Render Env")
    while True:
        time.sleep(60)

bot=telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)

CACHE={'prices':{}, 'time':0}
LAST_TITLES=set()

def get_prices():
    if time.time()-CACHE['time']<120 and CACHE['prices']:
        return CACHE['prices']
    prices={}
    try:
        import yfinance as yf
        for sym in ['CL=F','^NSEI','USO']:
            try:
                h=yf.Ticker(sym).history(period='5d')
                if h.empty: continue
                c=float(h['Close'].iloc[-1])
                p2=float(h['Close'].iloc[-2]) if len(h)>1 else c
                ch=0
                if p2!=0: ch=(c-p2)/p2*100
                v1=float(h['Volume'].iloc[-1])
                v2=float(h['Volume'].tail(5).mean())
                prices[sym]={'price':c,'change':ch,'vol':v1,'vavg':v2}
            except: continue
    except: pass
    if prices:
        CACHE['prices']=prices
        CACHE['time']=time.time()
    return CACHE['prices']

def get_breaking():
    try:
        import feedparser
        url='https://news.google.com/rss/search?q=crude+oil+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r=requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=8)
        feed=feedparser.parse(r.content)
        p=get_prices()
        cr=91.85
        if 'CL=F' in p: cr=p['CL=F']['price']
        for e in feed.entries:
            title=e.title.strip()
            link=e.link
            clean_title=title.split(' - ')[0].strip()
            source=title.split(' - ')[-1] if ' - ' in title else 'News'
            if clean_title in LAST_TITLES:
                continue
            low=clean_title.lower()
            if 'war' in low or 'attack' in low or 'killed' in low or 'cut' in low or 'crisis' in low or 'sanction' in low:
                impact='BULLISH 90% UP ⬆️'
            elif 'down' in low or 'fall' in low or 'supply' in low or 'increase' in low or 'surplus' in low:
                impact='BEARISH 90% DOWN ⬇️'
            else:
                impact='SIDEWAY 50% 👀'
            LAST_TIT
