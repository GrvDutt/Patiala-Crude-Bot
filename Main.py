# -*- coding: utf-8 -*-
# CRUDE BOT v12.0 NOVA - LINK ARROW EDITION - FINAL CLEAN
import os, threading, time, requests, pytz, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# --- HEALTH ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b'OK v12.0 NOVA')
    def do_HEAD(self): self.send_response(200); self.end_headers()
    def log_message(self,*a): pass

def run_health():
    HTTPServer(('0.0.0.0', int(os.environ.get('PORT',10000))), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

# --- CONFIG ---
BOT_TOKEN=os.getenv('BOT_TOKEN')
GROUP_ID=os.getenv('GROUP_ID','-1004448478970')
if not BOT_TOKEN: raise Exception("BOT_TOKEN missing")
bot=telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False, disable_web_page_preview=True)
try: bot.delete_webhook(drop_pending_updates=True)
except: pass

IST=pytz.timezone('Asia/Kolkata')
pinned_id=None
CACHE={'prices':{}, 'news':'Loading...', 'time':0}
USER_ALERTS=[]; ALERT_ID=0
LAST_BIG=set(); LAST_BIG_BUYER=0

SYMBOLS=['CL=F','^NSEI','^BSESN','GC=F','INR=X','USO']
SYMBOL_MAP={'crude':'CL=F','cl':'CL=F','oil':'CL=F','nifty':'^NSEI','sensex':'^BSESN','gold':'GC=F','uso':'USO'}

def get_prices():
    if time.time()-CACHE['time']<120 and CACHE['prices']:
        return CACHE['prices']
    prices={}
    try:
        import yfinance as yf
        for sym in SYMBOLS:
            try:
                h=yf.Ticker(sym).history(period='5d')
                if not h.empty:
                    c=float(h['Close'].iloc[-1]); p=float(h['Close'].iloc[-2]) if len(h)>1 else c
                    ch=(c-p)/p*100 if p else 0
                    vol=float(h['Volume'].iloc[-1]); vavg=float(h['Volume'].tail(5).mean()) if len(h)>=5 else vol
                    prices[sym]={'price':c,'change':ch,'vol':vol,'vavg':vavg}
            except: continue
    except: pass
    if prices: CACHE['prices']=prices; CACHE['time']=time.time()
    return CACHE['prices']

# --- NEWS WITH LINK + ARROW ---
def fetch_news():
    try:
        import feedparser
        url='https://news.google.com/rss/search?q=crude+oil+OPEC+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=6)
        feed=feedparser.parse(r.content)
        txt='';
        for i,e in enumerate(feed.entries[:5],1):
            t=e.title[:80].replace('<','').replace('>','')
