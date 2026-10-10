# -*- coding: utf-8 -*-
# CRUDE BOT v12.5 NOVA - ULTRA SIMPLE NO ELIF NO AND ERROR
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
        self.wfile.write(b'OK v12.5')
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
LAST_BIG=set()
LAST_BIG_BUYER=0
SYMBOLS=['CL=F','USO']

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
                c2=float(h['Close'].iloc[-2]) if len(h)>1 else c
                ch=0
                if c2!=0:
                    ch=(c-c2)/c2*100
                v1=float(h['Volume'].iloc[-1])
                v2=float(h['Volume'].tail(5).mean())
                prices[sym]={'price':c,'change':ch,'vol':v1,'vavg':v2}
            except:
                continue
    except:
        pass
    if prices:
        CACHE['prices']=prices
        CACHE
