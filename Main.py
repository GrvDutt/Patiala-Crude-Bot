# Main.py v17.6 FIXED - No Syntax Error
import os, threading, time, requests, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'OK v17.6 FIXED')
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
    while True: time.sleep(60)

bot=telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)
CACHE={'prices':{}, 'time':0, 'inr':88.5}
LAST=set()
LAST_NEWS={'title':'Crude Oil Mixed','imp':'SIDEWAY 50%','link':'https://news.google.com/search?q=crude+oil'}

def get_inr():
    try:
        import yfinance as yf
        h=yf.Ticker('USDINR=X').history(period='1d')
        if not h.empty: return float(h['Close'].iloc[-1])
    except: pass
    return CACHE['inr']

def calc_rsi(prices, period=14):
    if len(prices)<period+1: return 50
    import numpy as np
    deltas=np.diff(prices)
    gains=deltas.clip(min=0); losses=-deltas.clip(max=0)
    avg_gain=np.mean(gains[-period:]); avg_loss=np.mean(losses[-period:])
    if avg_loss==0: return 100
    rs=avg_gain/avg_loss
    return 100 - (100/(1+rs))

def get_prices():
    now=time.time()
    if now - CACHE['time'] < 60 and CACHE['prices']: return CACHE['prices']
    prices={}; inr=get_inr(); CACHE['inr']=inr
    try:
        import yfinance as yf, numpy as np
        t=yf.Ticker('CL=F')
        h5=t.history(period='5d')
        h1d=t.history(period='1d', interval='1h')
        h1m=t.history(period='1d', interval='1m')
        if not h5.empty:
            live=float(h5['Close'].iloc[-1])
            prev=float(h5['Close'].iloc[-2]) if len(h5)>1 else live
            open_p=float(h5['Open'].iloc[-1])
            high_y=float(h5['High'].iloc[-2]) if len(h5)>1 else live
            low_y=float(h5['Low'].iloc[-2]) if len(h5)>1 else live
            vol_today=float(h5['Volume'].iloc[-1]) if 'Volume' in h5.columns else 0
            vol_yday=float(h5['Volume'].iloc[-2]) if len(h5)>1 else 0
            vol_avg=float(h5['Volume'].mean()) if 'Volume' in h5.columns else 0
            vol_ratio=vol_today/vol_avg if vol_avg else 1
            vol_1h=float(h1d['Volume'].iloc[-1]) if not h1d.empty else 0
            vol_1h_prev=float(h1d['Volume'].iloc[-2]) if not h1d.empty and len(h1d)>1 else 0
            week_ch=(live - float(h5['Close'].iloc[0]))/float(h5['Close'].iloc[0])*100 if len(h5)>0 else 0
            h1_from=live; h1_ch=0
            if not h1d.empty and len(h1d)>=2:
                h1_from=float(h1d['Close'].iloc[-2])
                h1_ch=(live - h1_from)/h1_from*100 if h1_from else 0
            ema9=0; ema21=0; rsi=50; mom_5m=0; trend_1m="SIDEWAY"
            if not h1m.empty and len(h1m)>21:
                closes=h1m['Close'].values
                ema9=float(np.mean(closes[-9:]))
                ema21=float(np.mean(closes[-21:]))
                rsi=calc_rsi(closes)
                if len(closes)>=5:
                    mom_5m=(closes[-1]-closes[-5])/closes[-5]*100
                if closes[-1]>closes[-2]:
                    trend_1m="UP 🚀"
                else:
                    trend_1m="DOWN 📉"
            prices['CL=F']={'price':live,'change':(live-prev)/prev*100 if prev else 0,'open':open_p,'prev':prev,'high_y':high_y,'low_y':low_y,'avg_y':(high_y+low_y)/2,'week_ch':week_ch,'h1_ch':h1_ch,'h1_from':h1_from,'inr':inr,'vol':vol_today,'vol_yday':vol_yday,'vol_avg':vol_avg,'vol_ratio':vol_ratio,'vol_1h':vol_1h,'vol_1h_prev':vol_1h_prev,'ema9':ema9,'ema21':ema21,'rsi':rsi,'mom_5m':mom_5m,'trend_1m':trend_1m}
    except Exception as e: print("price err",e)
    if prices: CACHE['prices']=prices; CACHE['time']=now
    return prices if prices else CACHE['prices']

def analyze_news_impact(title, cr):
    low=title.lower()
    live=cr.get('price',90)
    open_p=cr.get('open',90)
    h1_ch=cr.get('h1_ch',0)
    supply_down=False
    supply_up=False
    if 'production low' in low or 'output cut' in low or 'well destroy' in low or 'well damaged' in low or 'opec cut' in low or 'supply cut' in low or 'supply low' in low:
        supply_down=True
    if 'production high' in low or 'output rise' in low or 'supply rise' in low or 'opec increase' in low:
        supply_up=True
    expected="SIDEWAY"
    if supply_down: expected="UP"
    if 'war' in low or 'attack' in low: expected="UP"
    if 'demand high' in low or 'demand rise' in low: expected="UP"
    if supply_up: expected="DOWN"
    if 'demand low' in low or 'demand fall' in low: expected="DOWN"
    actual="SIDEWAY"
    if live>open_p and h1_ch>-0.1:
        actual="UP"
    elif h1_ch>0.2:
        actual="UP"
    elif h1_ch<-0.1:
        actual="DOWN"
    else:
        actual="SIDEWAY"
    paradox=False
    if expected=="UP" and actual=="DOWN": paradox=True
    if expected=="DOWN" and actual=="UP": paradox=True
    return expected, actual, paradox, supply_down, supply_up

def get_volume_prediction(cr):
    vol_ratio=cr.get('vol_ratio',1)
    h1_ch=cr.get('h1_ch',0)
    if vol_ratio>1.5 and h1_ch>0.1:
        return f"📈 VOL: Shark BUYING 🔥 {round(vol_ratio,2)}x HIGH + Price UP = UPAR JAYEGA 🚀"
    if vol_ratio>1.5 and h1_ch<-0.1:
        return f"📉 VOL: Shark SELLING 🐋 {round(vol_ratio,2)}x HIGH + Price DOWN = NICHE JAYEGA 🔻"
    if vol_ratio<0.7 and h1_ch>0:
        return f"⚠️ VOL: TRAP 🐟 LOW {round(vol_ratio,2)}x + UP = FAKE PUMP"
    if vol_ratio<0.7 and h1_ch<0:
        return f"💤 VOL: WEAK Selling LOW {round(vol_ratio,2)}x = BOUNCE AYEGA 🔼"
    return f"➡️ VOL: Normal {round(vol_ratio,2)}x, Trend follow karo"

def get_smart_ai(news_title, news_imp, cr, user_q=""):
    live=cr.get('price',90)
    open_p=cr.get('open',90)
    h1_ch=cr.get('h1_ch',0)
    vol_ratio=cr.get('vol_ratio',1)
    rsi=cr.get('rsi',50)
    ema9=cr.get('ema9',0)
    ema21=cr.get('ema21',0)
    mom_5m=cr.get('mom_5m',0)
    expected, actual, paradox, s_down, s_up = analyze_news_impact(news_title+" "+news_imp, cr)
    score=0
    reasons=[]
    if live>open_p:
        score+=1
        reasons.append("Live Open se upar")
    else:
        score-=1
        reasons.append("Live Open se niche")
    if h1_ch>0.2:
        score+=2
        reasons.append(f"1H {round(h1_ch,2)}% upar")
    elif h1_ch<-0.2:
        score-=2
        reasons.append(f"1H {round(h1_ch,2)}% niche")
    if vol_ratio>1.2 and h1_ch>0:
        score+=2
        reasons.append(f"Vol HIGH {round(vol_ratio,2)}x buying")
    if vol_ratio>1.2 and h1_ch<0:
        score-=2
        reasons.append(f"Vol HIGH {round(vol_ratio,2)}x selling")
    if rsi>70:
        score-=1
        reasons.append(f"RSI {round(rsi,0)} Overbought")
    elif rsi<30:
        score+=1
        reasons.append(f"RSI {round(rsi,0)} Oversold")
    else:
        reasons.append(f"RSI {round(rsi,0)} normal")
    if ema9>ema21:
        score+=1
        reasons.append("EMA Golden Cross")
    else:
        score-=1
        reasons.append("EMA Death Cross")
    if mom_5m>0.1:
        score+=1
    elif mom_5m<-0.1:
        score-=1
    base_explain=""
    if s_down:
        base_explain="🗞️ News: Production LOW / Well destroy = Supply KAM = UPAR jana chahiye tha 🚀"
    elif s_up:
        base_explain="🗞️ News: Production HIGH = Supply ZYADA = NICHE jana chahiye tha 📉"
    else:
        base_explain=f"🗞️ News: {news_title[:70]}"
    paradox_explain=""
    if paradox and expected=="UP" and actual=="DOWN":
        paradox_explain=f"\n\n🤔 PAR LOGIC: News UP wali hai par Market DOWN {round(h1_ch,2)}% kyu?\n1. Dollar strong\n2. Profit booking\n3. News priced-in hai"
    if paradox and expected=="DOWN" and actual=="UP":
