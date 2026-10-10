# -*- coding: utf-8 -*-
# CRUDE BOT v12.4 NOVA - FINAL NO SYNTAX ERROR
import os
import threading
import time
import requests
import telebot
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v12.4')
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self,*a):
        pass

def run_health():
    port = int(os.environ.get('PORT','10000'))
    HTTPServer(('0.0.0.0', port), H).serve_forever()

threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN=os.getenv('BOT_TOKEN')
GROUP_ID=os.getenv('GROUP_ID','-1004448478970')
bot=telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)

CACHE={'prices':{}, 'time':0}
USER_ALERTS=[]
ALERT_ID=0
LAST_BIG=set()
LAST_BIG_BUYER=0
SYMBOLS=['CL=F','^NSEI','^BSESN','GC=F','USO']

def get_prices():
    if time.time()-CACHE['time']<120 and CACHE['prices']:
        return CACHE['prices']
    prices={}
    try:
        import yfinance as yf
        for sym in SYMBOLS:
            try:
                h=yf.Ticker(sym).history(period='5d')
                if h.empty:
                    continue
                c=float(h['Close'].iloc[-1])
                p2=float(h['Close'].iloc[-2]) if len(h)>1 else c
                ch=0
                if p2!=0:
                    ch=(c-p2)/p2*100
                v1=float(h['Volume'].iloc[-1])
                v2=float(h['Volume'].tail(5).mean())
                prices[sym]={'price':c,'change':ch,'vol':v1,'vavg':v2}
            except Exception:
                continue
    except Exception:
        pass
    if prices:
        CACHE['prices']=prices
        CACHE['time']=time.time()
    return CACHE['prices']

def send_breaking_news(to_group=True):
    try:
        import feedparser
        url='https://news.google.com/rss/search?q=crude+oil+OPEC+Iran+war+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r=requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=6)
        feed=feedparser.parse(r.content)
        p=get_prices()
        cr=p.get('CL=F',{'price':91.85})['price']
        for e in feed.entries[:2]:
            if to_group and e.title in LAST_BIG:
                continue
            if to_group:
                LAST_BIG.add(e.title)
            low=e.title.lower()
            if 'war' in low or 'attack' in low or 'killed' in low or 'crisis' in low or 'cut' in low:
                impact='BULLISH 90% UP'
            elif 'down' in low or 'fall' in low or 'increase' in low or 'supply' in low:
                impact='BEARISH 90% DOWN'
            else:
                impact='SIDEWAY 50%'
            msg="BREAKING - CRUDE IMPACT\n\n" + e.title + "\n\nIMPACT: " + impact + "\nCrude: $" + str(round(cr,2))
            if not to_group:
                return msg
            bot.send_message(int(GROUP_ID), msg)
            return msg
        if not to_group:
            return "BREAKING - CRUDE IMPACT\nMarket stable Crude $" + str(round(cr,2))
    except Exception as ex:
        return "News loading " + str(ex)

def check_big_buyers():
    global LAST_BIG_BUYER
    if time.time()-LAST_BIG_BUYER<1800:
        return
    try:
        p=get_prices()
        uso=p.get('USO')
        cr=p.get('CL=F',{'price':91})
        if not uso:
            return
        if uso['vol']>uso['vavg']*1.5 and uso['change']>1.0:
            bot.send_message(int(GROUP_ID), "BIG BUYER LIVE\nUSO " + str(round(uso['vol']/1e6,1)) + "M vol pump " + str(round(uso['change'],2)) + "%\nCrude $" + str(round(cr['price'],2)))
            LAST_BIG_BUYER=time.time()
        elif uso['vol']>uso['vavg']*1.5 and uso
