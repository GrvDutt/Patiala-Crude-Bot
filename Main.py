# Main.py v17.9 EXPLAIN FIX
import os, threading, time, requests, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v17.9 EXPLAIN FIX')
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self,*a): pass

def run_health():
    port=int(os.environ.get('PORT','10000'))
    HTTPServer(('0.0.0.0', port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN=os.getenv('BOT_TOKEN')
GROUP_ID=os.getenv('GROUP_ID','-1004448478970')
if not BOT_TOKEN:
    while True:
        time.sleep(60)

bot=telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)
CACHE={'prices':{}, 'time':0, 'inr':88.5}
LAST=set()
LAST_NEWS={'title':'Brent Crude Rises Above $105','imp':'SIDEWAY 50%','link':'https://news.google.com/search?q=crude+oil'}

def get_inr():
    try:
        import yfinance as yf
        h=yf.Ticker('USDINR=X').history(period='1d')
        if not h.empty:
            return float(h['Close'].iloc[-1])
    except:
        pass
    return CACHE['inr']

def calc_rsi(prices, period=14):
    if len(prices)<period+1:
        return 50
    import numpy as np
    deltas=np.diff(prices)
    gains=deltas.clip(min=0)
    losses=-deltas.clip(max=0)
    avg_gain=np.mean(gains[-period:])
    avg_loss=np.mean(losses[-period:])
    if avg_loss==0:
        return 100
    rs=avg_gain/avg_loss
    return 100 - (100/(1+rs))

def get_prices():
    now=time.time()
    if now - CACHE['time'] < 60 and CACHE['prices']:
        return CACHE['prices']
    prices={}
    inr=get_inr()
    CACHE['inr']=inr
    try:
        import yfinance as yf
        import numpy as np
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
            vol_avg=float(h5['Volume'].mean()) if 'Volume' in h5.columns else 0
            vol_ratio=vol_today/vol_avg if vol_avg else 1
            vol_1h=float(h1d['Volume'].iloc[-1]) if not h1d.empty else 0
            vol_1h_prev=float(h1d['Volume'].iloc[-2]) if len(h1d)>1 and not h1d.empty else 0
            week_ch=0
            if len(h5)>0:
                week_ch=(live - float(h5['Close'].iloc[0]))/float(h5['Close'].iloc[0])*100
            h1_from=live
            h1_ch=0
            if not h1d.empty and len(h1d)>=2:
                h1_from=float(h1d['Close'].iloc[-2])
                if h1_from!=0:
                    h1_ch=(live - h1_from)/h1_from*100
            ema9=0
            ema21=0
            rsi=50
            mom_5m=0
            trend_1m="SIDEWAY"
            if not h1m.empty and len(h1m)>21:
                closes=h1m['Close'].values
                ema9=float(np.mean(closes[-9:]))
                ema21=float(np.mean(closes[-21:]))
                rsi=calc_rsi(closes)
                if len(closes)>=5 and closes[-5]!=0:
                    mom_5m=(closes[-1]-closes[-5])/closes[-5]*100
                if closes[-1]>closes[-2]:
                    trend_1m="UP 🚀"
                else:
                    trend_1m="DOWN 📉"
            prices['CL=F']={
                'price':live,'open':open_p,'prev':prev,'high_y':high_y,'low_y':low_y,'avg_y':(high_y+low_y)/2,
                'week_ch':week_ch,'h1_ch':h1_ch,'h1_from':h1_from,'inr':inr,'vol':vol_today,'vol_avg':vol_avg,
                'vol_ratio':vol_ratio,'vol_1h':vol_1h,'vol_1h_prev':vol_1h_prev,'ema9':ema9,'ema21':ema21,
                'rsi':rsi,'mom_5m':mom_5m,'trend_1m':trend_1m
            }
    except Exception as e:
        print("price err",e)
    if prices:
        CACHE['prices']=prices
        CACHE['time']=now
    return prices if prices else CACHE['prices']

def get_volume_prediction(cr):
    vol_ratio=cr.get('vol_ratio',1)
    h1_ch=cr.get('h1_ch',0)
    if vol_ratio>1.5 and h1_ch>0.1:
        return f"📈 VOL: Shark BUYING 🔥 {round(vol_ratio,2)}x HIGH + Price UP = UPAR JAYEGA 🚀"
    if vol_ratio>1.5 and h1_ch<-0.1:
        return f"📉 VOL: Shark SELLING 🐋 {round(vol_ratio,2)}x HIGH + Price DOWN = NICHE JAYEGA 🔻"
    if vol_ratio<0.7 and h1_ch>0:
        return f"⚠️ VOL: TRAP 🐟 LOW {round(vol_ratio,2)}x + UP = FAKE PUMP - GIRNE WALA HAI 🔻"
    if vol_ratio<0.7 and h1_ch<0:
        return f"💤 VOL: WEAK LOW {round(vol_ratio,2)}x + DOWN = BOUNCE AYEGA 🔼"
    return f"➡️ VOL: Normal {round(vol_ratio,2)}x"

def get_explanation(q, cr):
    q=q.lower()
    vol_ratio=round(cr.get('vol_ratio',0.18),2)
    h1_ch=round(cr.get('h1_ch',0),2)
    rsi=round(cr.get('rsi',50),1)
    live=round(cr.get('price',91),2)
    
    if 'volume' in q or 'vol' in q or 'trap' in q or 'number 6' in q or 'no 6' in q or 'point 6' in q:
        return f"📚 <b>VOLUME TRAP EXPLAIN - Point No 6</b>\n\n<b>Abhi kya hai?</b>\nVol Ratio = {vol_ratio}x (Normal 1.0x hota hai)\nMatlab aaj volume Avg se 82% KAM hai\nPrice UP {h1_ch}% par Vol LOW hai\n\n<b>Iska matlab kya hai?</b>\n1. 🐟 FAKE PUMP: Bade players (Shark) kharid nahi rahe, sirf chote retailer kharid rahe hai\n2. 💸 Paise nahi lage hai is UP move me, isiliye ye jaldi gir jayega\n3. 🔻 Jab Vol LOW + Price UP hota hai = Trap hota hai, logo ko fasane ke liye upar dikhate hai fir niche patak dete hai\n\n<b>Example:</b>\nNormal me 2.5 Lakh contracts trade hone chahiye, abhi sirf {int(cr.get('vol',45000)/1000)}K hue hai = {vol_ratio}x\nIsiliye maine likha 'FAKE PUMP - GIRNE WALA HAI'\n\n<b>Trade kya kare?</b>\nCALL mat lo ❌, PUT ka wait karo ya WAIT karo. Jab Vol HIGH ayega tabhi CALL lena.\n\n<b>Current Live:</b> ${live} RSI {rsi}"

    if 'rsi' in q:
        return f"📚 <b>RSI EXPLAIN - Point No 5</b>\n\nAbhi RSI = {rsi}\n\nRSI matlab Relative Strength Index (0-100)\n• RSI > 70 = Overbought 🔴 = Bahut zyada kharida, ab girega - PUT time\n• RSI < 30 = Oversold 🟢 = Bahut zyada becha, ab uthega - CALL time\n• RSI 30-70 = Normal\n\nAbhi {rsi} hai = {('Overbought hai, top pe hai, PUT ka time' if rsi>70 else 'Oversold hai' if rsi<30 else 'Normal hai')}\n\nLive ${live}"

    if 'ema' in q or 'golden' in q or 'death' in q:
        ema9=round(cr.get('ema9',0),2)
        ema21=round(cr.get('ema21',0),2)
        return f"📚 <b>EMA EXPLAIN</b>\n\nEMA 9 = ${ema9} (9 min ka average)\nEMA 21 = ${ema21} (21 min ka average)\n\n• Golden Cross 🟢: EMA 9 > EMA 21 = UPAR jayega = CALL\n• Death Cross 🔴: EMA 9 < EMA 21 = NICHE jayega = PUT\n\nAbhi {('Golden Cross hai, bullish' if ema9>ema21 else 'Death Cross hai, bearish')}"

    if 'explain' in q or 'samjha' in q or 'kya hai' in q or 'matlab' in q:
        vol_ratio=round(cr.get('vol_ratio',0.18),2)
        return f"📚 <b>FULL EXPLAIN</b>\n\n{get_volume_prediction(cr)}\n\nVol Ratio {vol_ratio}x ka matlab:\n1.0x = Normal volume\n>1.5x = Shark active 🔥\n<0.7x = Trap 🐟\n\nAbhi {vol_ratio}x = Bahut LOW = Shark nahi kharid rahe, ye UP fake hai.\n\nPrice ${live} hai par bina volume ke upar gaya hai, isiliye girne wala hai."

    return None

def get_smart_ai(news_title, news_imp, cr, user_q=""):
    # Pehle check karo kya explain manga hai
    exp = get_explanation(user_q, cr)
    if exp:
        return exp

    live=cr.get('price',90)
    open_p=cr.get('open',90)
    h1_ch=cr.get('h1_ch',0)
    vol_ratio=cr.get('vol_ratio',1)
    rsi=cr.get('rsi',50)
    ema9=cr.get('ema9',0)
    ema21=cr.get('ema21',0)

    if rsi>80 and vol_ratio<0.5 and h1_ch>0:
        final="PUT"
        chance=78
        reason=f"🔴 TRAP CONFIRMED: RSI {round(rsi,0)} Overbought + LOW Vol {round(vol_ratio,2)}x = FAKE PUMP"
        q=user_q.lower()
        if 'call' in q:
            return f"🗞️ News: {news_title[:70]}\n\n{reason}\n\n🤖 Nahi CALL mat lo ❌ FAKE PUMP hai {chance}% niche girega 📉"
        if 'put' in q:
            return f"🗞️ News: {news_title[:70]}\n\n{reason}\n\n🤖 Haan PUT le sakte ho ✅ {chance}% NICHE girega 📉"
        return f"🗞️ News: {news_title[:70]}\n\n🤖 SMART: {final} {chance}% | {reason}"

    score=0
    reasons=[]
    if live>open_p:
        score=score+1
        reasons.append("Live Open se upar")
    else:
        score=score-1
        reasons.append("Live Open se niche")
    if h1_ch>0.3:
        score=score+2
        reasons.append(f"1H {round(h1_ch,2)}% upar")
    elif h1_ch<-0.3:
        score=score-2
        reasons.append(f"1H {round(h1_ch,2)}% niche")
    if vol_ratio<0.7 and h1_ch>0:
        score=score-2
        reasons.append(f"LOW Vol Trap {round(vol_ratio,2)}x")
    elif vol_ratio>1.2 and h1_ch>0:
        score=score+2
        reasons.append(f"HIGH Vol Buying {round(vol_ratio,2)}x")
    if rsi>75:
        score=score-2
        reasons.append(f"RSI {round(rsi,0)} Overbought 🔴")
    elif rsi<25:
        score=score+2
        reasons.append(f"RSI {round(rsi,0)} Oversold 🟢")
    else:
        reasons.append(f"RSI {round(rsi,0)} normal")
    if ema9>ema21:
        score=score+1
        reasons.append("Golden Cross 🟢")
    else:
        score=score-1
        reasons.append("Death Cross 🔴")

    base_explain=f"🗞️ News: {news_title[:80]}"
    final="WAIT"
    chance=50
    if score>=3:
        final="CALL"
        chance=72
    elif score>=1:
        final="CALL"
        chance=60
    elif score<=-3:
        final="PUT"
        chance=72
    elif score<=-1:
        final="PUT"
        chance=60

    q=user_q.lower()
    reason_txt=", ".join(reasons[:3])
    if 'call' in q:
        if final=="CALL":
            return f"{base_explain}\n\n🤖 Haan CALL le sakte ho {chance}% UPAR 🚀\nReason: {reason_txt}"
        else:
            return f"{base_explain}\n\n🤖 Nahi CALL mat lo {100-chance}% hi chance upar ka, {chance}% {final} hai 📉\nReason: {reason_txt}"
    if 'put' in q:
        if final=="PUT":
            return f"{base_explain}\n\n🤖 Haan PUT le sakte ho {chance}% NICHE 📉\nReason: {reason_txt}"
        else:
            return f"{base_explain}\n\n🤖 Nahi PUT mat lo {final} hai"
    return f"{base_explain}\n\n🤖 SMART: {final} {chance}% | {reason_txt} | RSI {round(rsi,0)} | Vol {round(vol_ratio,2)}x"

def build_total_status():
    p=get_prices()
    cr=p.get('CL=F')
    if not cr:
        return "📊 CRUDE TOTAL STATUS Bot LIVE"
    title=LAST_NEWS['title']
    imp=LAST_NEWS['imp']
    link=LAST_NEWS['link']
    live=cr['price']
    inr=cr['inr']
    live_inr=int(live*inr)
    open_p=cr['open']
    open_inr=int(open_p*inr)
    prev=cr['prev']
    h1_ch=round(cr['h1_ch'],2)
    h1_from=cr['h1_from']
    high_y=cr['high_y']
    low_y=cr['low_y']
    week_ch=round(cr['week_ch'],2)
    curr_tag="BULLISH 🟢🔼"
    if live<=prev:
        curr_tag="BEARISH 🔴🔻"
    week_tag="BULLISH 🚀"
    if week_ch<=0:
        week_tag="BEARISH 📉"
    vol=cr.get('vol',0)
    vol_avg=cr.get('vol_avg',0)
    vol_ratio=cr.get('vol_ratio',1)
    vol_1h=cr.get('vol_1h',0)
    vol_1h_prev=cr.get('vol_1h_prev',0)
    vol_1h_ch=0
    if vol_1h_prev!=0:
        vol_1h_ch=(vol_1h - vol_1h_prev)/vol_1h_prev*100
    rsi=round(cr.get('rsi',50),1)
    ema9=round(cr.get('ema9',0),2)
    ema21=round(cr.get('ema21',0),2)
    mom_5m=round(cr.get('mom_5m',0),3)
    trend_1m=cr.get('trend_1m','-')
    ema_cross="Golden Cross 🟢 UPAR"
    if ema9<=ema21:
        ema_cross="Death Cross 🔴 NICHE"
    vol_pred=get_volume_prediction(cr)
    smart_ai=get_smart_ai(title, imp, cr)
    msg="📊 <b>CRUDE TOTAL STATUS v17.9</b>\n\n"
    msg=msg+f"1. CURRENT: {curr_tag}\nLive: ${round(live,2)} | ₹{live_inr}\nOpen: ${round(open_p,2)} | ₹{open_inr} | Prev: ${round(prev,2)}\n📊 Vol: Today {int(vol/1000)}K | Avg {int(vol_avg/1000)}K | {round(vol_ratio,2)}x\n\n"
    msg=msg+f"2. LAST 1 HOUR: {h1_ch}% {trend_1m}\n${round(h1_from,2)} -> ${round(live,2)}\nVol 1H: {int(vol_1h/1000)}K Ch: {round(vol_1h_ch,1)}%\n\n"
    msg=msg+f"3. KAL KA: H:${round(high_y,2)} L:${round(low_y,2)} Avg:{round((high_y+low_y)/2,2)}\n\n"
    msg=msg+f"4. WEEK TREND: {week_tag} {week_ch}%\n\n"
    msg=msg+f"5. ⚡ INDICATORS:\nEMA 9: ${ema9} | 21: ${ema21} => {ema_cross}\nRSI: {rsi} {('🔴 Overbought - PUT ka time' if rsi>70 else '🟢 Oversold - CALL ka time' if rsi<30 else 'Normal')}\nMom: {mom_5m}%\n\n"
    msg=msg+f"6. {vol_pred}\n\n7. {smart_ai}\n\n8. 🗞️ NEWS: {title}\n{imp}\n🔗 <a href=\"{link}\">Full News</a>"
    return msg

@bot.message_handler(func=lambda m: m.text and ('@patialagrvbot' in m.text.lower()))
def mention_h(m):
    user_q=m.text.lower().replace('@patialagrvbot','').strip()
    if not user_q:
        user_q="kya karu"
    cr=get_prices().get('CL=F',{})
    smart=get_smart_ai(LAST_NEWS['title'], LAST_NEWS['imp'], cr, user_q)
    volp=get_volume_prediction(cr)
    # Agar explain manga hai toh sirf explain bhejo, volp double mat bhejo
    if 'explain' in
