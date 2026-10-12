# -*- coding: utf-8 -*-
# Main.py v16.8 SINGLE FILE - Emoji + Conversation Fixed
import os, threading, time, requests, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v16.8 FULL')
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self,*a): pass

def run_health():
    port = int(os.environ.get('PORT','10000'))
    HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = os.getenv('GROUP_ID','-1004448478970')
if not BOT_TOKEN:
    while True: time.sleep(60)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)
CACHE = {'prices':{}, 'time':0, 'inr':88.5}
LAST = set()
LAST_NEWS = {'title':'Indian Stocks Rise as Crude Oil Falls','imp':'BEARISH 🔻 70% niche','link':'https://news.google.com/search?q=crude+oil'}
ALERTS = []

def get_inr():
    try:
        import yfinance as yf
        h = yf.Ticker('USDINR=X').history(period='1d')
        if not h.empty: return float(h['Close'].iloc[-1])
    except: pass
    return CACHE['inr']

def get_prices():
    now = time.time()
    if now - CACHE['time'] < 120 and CACHE['prices']: return CACHE['prices']
    prices = {}; inr = get_inr(); CACHE['inr']=inr
    try:
        import yfinance as yf
        t = yf.Ticker('CL=F')
        h5 = t.history(period='5d')
        h1d = t.history(period='1d', interval='1h')
        if not h5.empty:
            live = float(h5['Close'].iloc[-1])
            prev = float(h5['Close'].iloc[-2]) if len(h5)>1 else live
            open_p = float(h5['Open'].iloc[-1])
            high_y = float(h5['High'].iloc[-2]) if len(h5)>1 else live
            low_y = float(h5['Low'].iloc[-2]) if len(h5)>1 else live
            avg_y = (high_y+low_y)/2
            vol_today = float(h5['Volume'].iloc[-1]) if 'Volume' in h5.columns else 0
            vol_yday = float(h5['Volume'].iloc[-2]) if len(h5)>1 and 'Volume' in h5.columns else 0
            vol_avg = float(h5['Volume'].mean()) if 'Volume' in h5.columns else 0
            vol_ratio = vol_today / vol_avg if vol_avg else 1
            vol_change = ((vol_today - vol_yday)/vol_yday*100) if vol_yday else 0
            vol_1h = float(h1d['Volume'].iloc[-1]) if not h1d.empty and 'Volume' in h1d.columns else 0
            vol_1h_prev = float(h1d['Volume'].iloc[-2]) if not h1d.empty and len(h1d)>1 else 0
            week_ch = (live - float(h5['Close'].iloc[0]))/float(h5['Close'].iloc[0])*100 if len(h5)>0 else 0
            h1_from = live; h1_ch=0
            if not h1d.empty and len(h1d)>=2:
                h1_from = float(h1d['Close'].iloc[-2])
                h1_ch = (live - h1_from)/h1_from*100 if h1_from else 0
            prices['CL=F']={'price':live,'change':(live-prev)/prev*100 if prev else 0,'open':open_p,'prev':prev,'high_y':high_y,'low_y':low_y,'avg_y':avg_y,'week_ch':week_ch,'h1_ch':h1_ch,'h1_from':h1_from,'inr':inr,'vol':vol_today,'vol_yday':vol_yday,'vol_avg':vol_avg,'vol_ratio':vol_ratio,'vol_change':vol_change,'vol_1h':vol_1h,'vol_1h_prev':vol_1h_prev}
    except Exception as e: print("price err",e)
    if prices: CACHE['prices']=prices; CACHE['time']=now
    return prices if prices else CACHE['prices']

def get_market_status():
    try:
        now_utc = datetime.now(pytz.utc)
        et = now_utc.astimezone(pytz.timezone('America/New_York'))
        ist = now_utc.astimezone(pytz.timezone('Asia/Kolkata'))
        def is_open(dt, sh, sm, eh, em):
            if dt.weekday()>=5: return False
            mins=dt.hour*60+dt.minute
            return sh*60+sm <= mins <= eh*60+em
        return {'USA':is_open(et,9,30,16,0),'INDIA':is_open(ist,9,15,15,30),'MCX':is_open(ist,9,0,23,30),'times':{'ET':et.strftime('%I:%M %p'),'IST':ist.strftime('%I:%M %p')}}
    except: return {'USA':False,'INDIA':True,'MCX':True,'times':{}}

def get_global_markets_data():
    data={}; syms={'USA NASDAQ':'^IXIC','USA S&P500':'^GSPC','USA DOW':'^DJI','INDIA NIFTY':'^NSEI','INDIA SENSEX':'^BSESN','UK FTSE':'^FTSE','JAPAN Nikkei':'^N225'}
    try:
        import yfinance as yf
        for name,sym in syms.items():
            try:
                t=yf.Ticker(sym); h1d=t.history(period='1d'); h1w=t.history(period='5d')
                if not h1d.empty and not h1w.empty:
                    live=float(h1d['Close'].iloc[-1]); day_h=float(h1d['High'].iloc[-1]); day_l=float(h1d['Low'].iloc[-1]); week_h=float(h1w['High'].max()); week_l=float(h1
