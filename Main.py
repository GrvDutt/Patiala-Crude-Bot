# -*- coding: utf-8 -*-
# CRUDE BOT v11.8 FINAL - 24x7 - ALL IN ONE
import os, threading, time, requests, pytz, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# HEALTH SERVER FOR RENDER 24x7
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b'OK v11.8 24x7')
    def do_HEAD(self): self.send_response(200); self.end_headers()
    def log_message(self,*a): pass

def run_health():
    port=int(os.environ.get('PORT',10000))
    HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN=os.getenv('BOT_TOKEN')
GROUP_ID=os.getenv('GROUP_ID','-1004448478970')
if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not set")

bot=telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)
try: bot.delete_webhook(drop_pending_updates=True)
except: pass

IST=pytz.timezone('Asia/Kolkata')
pinned_id=None

CACHE={'prices':{}, 'news':{}, 'time':0}
LAST_BREAKING=set()
LAST_LEADER=set()
BREAKING_SENT={}
sent_us_today=set()
USER_ALERTS=[]
ALERT_ID=0
LAST_CRUDE_PRICE=0
LAST_ALERT_PCT={}

SYMBOLS=['CL=F','^NSEI','^BSESN','^GSPC','^IXIC','^DJI','GC=F','INR=X']
SYMBOL_MAP={'crude':'CL=F','cl':'CL=F','oil':'CL=F','nifty':'^NSEI','sensex':'^BSESN','dow':'^DJI','nasdaq':'^IXIC','sp':'^GSPC','s&p':'^GSPC','gold':'GC=F','inr':'INR=X'}

BREAKING_KW=['opec cut','production cut','output cut','slowing production','missile attack','attack on','houthi','hormuz','embargo','sanction','ban on oil','diesel reserve','oil reserve','spr release','eu reserve','refinery blast','war','opec+ meeting','emergency']
LEADERS=['Trump','Biden','Putin','MBS','Mohammed bin Salman','UAE','OPEC Secretary','Saudi']

def fetch_one(sym):
    try:
        import yfinance as yf
        h=yf.Ticker(sym).history(period='7d')
        if h.empty: return sym,None
        c=float(h['Close'].iloc[-1]); p=float(h['Close'].iloc[-2]) if len(h)>1 else c
        ch=((c-p)/p*100) if p else 0
        if sym=='CL=F':
            opn=float(h['Open'].iloc[-1]); high_y=float(h['High'].iloc[-2]); low_y=float(h['Low'].iloc[-2])
            atr=float((h['High']-h['Low']).rolling(14).mean().iloc[-1]) if len(h)>14 else 0.45
            return sym,{'price':c,'change':ch,'open':opn,'high_y':high_y,'low_y':low_y,'atr':atr,'full':h}
        return sym,{'price':c,'change':ch}
