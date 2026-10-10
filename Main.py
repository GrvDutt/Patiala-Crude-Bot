# -*- coding: utf-8 -*-
# CRUDE BOT v12.1 NOVA - WHALE FINAL - DALNA HAI
import os, threading, time, requests, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b'OK v12.1 WHALE FINAL')
    def do_HEAD(self): self.send_response(200); self.end_headers()
    def log_message(self,*a): pass

def run_health():
    HTTPServer(('0.0.0.0', int(os.environ.get('PORT','10000'))), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN=os.getenv('BOT_TOKEN')
GROUP_ID=os.getenv('GROUP_ID','-1004448478970')
bot=telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)

CACHE={'prices':{}, 'time':0}
USER_ALERTS=[]; ALERT_ID=0
LAST_BIG=set(); LAST_BIG_BUYER=0
pinned_id=None
SYMBOLS=['CL=F','^NSEI','^BSESN','GC=F','INR=X','USO']

def get_prices():
    if time.time()-CACHE['time']<120 and CACHE['prices']:
        return CACHE['prices']
    prices={}
    try:
        import yfinance as yf
        for sym in SYMBOLS:
            try:
                h=yf.Ticker(sym).history(period='5d')
                if h.empty: continue
                c=float(h['Close'].iloc[-1]); p=float(h['Close'].iloc[-2]) if len(h)>1 else c
                ch=(c-p)/p*100 if p else 0
                v1=float(h['Volume'].iloc[-1]); v2=float(h['Volume'].tail(5).mean())
                prices[sym]={'price':c,'change':ch,'vol':v1,'vavg':v2}
            except: continue
    except: pass
    if prices:
        CACHE['prices']=prices; CACHE['time']=time.time()
    return CACHE['prices']

def send_breaking_news(to_group=True):
    try:
        import feedparser
        url='https://news.google.com/rss/search?q=crude+oil+OPEC+Iran+war+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r=requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=6)
        feed=feedparser.parse(r.content)
        p=get_prices(); cr=p.get('CL=F',{'price':91.85})['price']
        for e in feed.entries[:2]:
            if to_group and e.title in LAST_BIG: continue
            if to_group: LAST_BIG.add(e.title)
            low=e.title.lower()
            if any(w in low for w in ['war','attack','killed','crisis','cut']): impact='BULLISH 90% UP ⬆️'
            elif any(w in low for w in ['down','fall','increase','supply']): impact='BEARISH 90% DOWN ⬇️'
            else: impact='SIDEWAY 50% 👀'
            msg=f'🚨 BREAKING - CRUDE IMPACT 🚨\n\n⚠️ {e.title}\n\n💥 IMPACT: {impact}\nCrude: ${cr:.2f}\n\n📰 News - Abhi'
            if not to_group: return msg
            bot.send_message(int(GROUP_ID), msg)
            return msg
        if not to_group:
            return f'🚨 BREAKING - CRUDE IMPACT 🚨\nMarket stable Crude ${cr:.2f} 👀'
    except:
        return 'News loading...'

def check_big_buyers():
    global LAST_BIG_BUYER
    if time.time()-LAST_BIG_BUYER<1800: return
    try:
        p=get_prices(); uso=p.get('USO'); cr=p.get('CL=F',{'price':91})
        if not uso: return
        if uso['vol']>uso['vavg']*1.5 and uso['change']>1.0:
            bot.send_message(int(GROUP_ID), f'🐋 BIG BUYER LIVE ⬆️\nUSO {uso["vol"]/1e6:.1f}M vol ({uso["vol"]/uso["vavg"]*100:.0f}%) pump +{uso["change"]:.2f}%\nCrude ${cr["price"]:.2f} ⬆️\nMarket pull hoga')
            LAST_BIG_BUYER=time.time()
        elif
