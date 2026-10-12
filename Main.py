# Main.py v17.7 FINAL CLEAN - 100% Deploy OK
import os, threading, time, requests, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v17.7 CLEAN')
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
LAST_NEWS={'title':'Crude Oil Mixed','imp':'SIDEWAY 50%','link':'https://news.google.com/search?q=crude+oil'}

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

def analyze_news_impact(title, cr):
    low=title.lower()
    live=cr.get('price',90)
    open_p=cr.get('open',90)
    h1_ch=cr.get('h1_ch',0)
    supply_down=False
    supply_up=False
    if 'production low' in low:
        supply_down=True
    if 'output cut' in low:
        supply_down=True
    if 'well destroy' in low:
        supply_down=True
    if 'opec cut' in low:
        supply_down=True
    if 'supply low' in low:
        supply_down=True
    if 'production high' in low:
        supply_up=True
    if 'supply rise' in low:
        supply_up=True
    expected="SIDEWAY"
    if supply_down:
        expected="UP"
    if 'war' in low or 'attack' in low:
        expected="UP"
    if 'demand high' in low:
        expected="UP"
    if supply_up:
        expected="DOWN"
    if 'demand low' in low:
        expected="DOWN"
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
    if expected=="UP" and actual=="DOWN":
        paradox=True
    if expected=="DOWN" and actual=="UP":
        paradox=True
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
        return f"💤 VOL: WEAK LOW {round(vol_ratio,2)}x = BOUNCE AYEGA 🔼"
    return f"➡️ VOL: Normal {round(vol_ratio,2)}x"

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
        score=score+1
        reasons.append("Live Open se upar")
    else:
        score=score-1
        reasons.append("Live Open se niche")
    if h1_ch>0.2:
        score=score+2
        reasons.append(f"1H {round(h1_ch,2)}% upar")
    elif h1_ch<-0.2:
        score=score-2
        reasons.append(f"1H {round(h1_ch,2)}% niche")
    if vol_ratio>1.2 and h1_ch>0:
        score=score+2
        reasons.append(f"Vol HIGH {round(vol_ratio,2)}x buying")
    if vol_ratio>1.2 and h1_ch<0:
        score=score-2
        reasons.append(f"Vol HIGH {round(vol_ratio,2)}x selling")
    if rsi>70:
        score=score-1
        reasons.append(f"RSI {round(rsi,0)} Overbought")
    elif rsi<30:
        score=score+1
        reasons.append(f"RSI {round(rsi,0)} Oversold")
    else:
        reasons.append(f"RSI {round(rsi,0)} normal")
    if ema9>ema21:
        score=score+1
        reasons.append("EMA Golden Cross")
    else:
        score=score-1
        reasons.append("EMA Death Cross")
    base_explain=""
    if s_down:
        base_explain="🗞️ News: Production LOW = Supply KAM = UPAR jana chahiye tha 🚀"
    elif s_up:
        base_explain="🗞️ News: Production HIGH = Supply ZYADA = NICHE jana chahiye tha 📉"
    else:
        base_explain=f"🗞️ News: {news_title[:80]}"
    paradox_explain=""
    if paradox and expected=="UP" and actual=="DOWN":
        paradox_explain=f"\n\n🤔 PAR LOGIC: News UP wali hai par Market DOWN {round(h1_ch,2)}% kyu? 1.Dollar strong 2.Profit booking 3.News priced-in"
    if paradox and expected=="DOWN" and actual=="UP":
        paradox_explain=f"\n\n🤔 PAR LOGIC: News DOWN wali hai par Market UP {round(h1_ch,2)}%? Shark buying"
    final="WAIT"
    chance=50
    if score>=3:
        final="CALL"
        chance=72
    elif score>=1:
        final="CALL"
        chance=61
    elif score<=-3:
        final="PUT"
        chance=72
    elif score<=-1:
        final="PUT"
        chance=61
    else:
        final="WAIT"
        chance=50
    q=user_q.lower()
    is_call=False
    is_put=False
    if 'call' in q or 'upar' in q or 'buy' in q:
        is_call=True
    if 'put' in q or 'niche' in q or 'short' in q:
        is_put=True
    explain_part=base_explain+paradox_explain
    reason_txt=", ".join(reasons[:3])
    if is_call:
        if final=="CALL":
            return f"{explain_part}\n\n🤖 Haan CALL le sakte ho {chance}% UPAR 🚀\nReason: {reason_txt}\nLive ${round(live,2)} Vol {round(vol_ratio,2)}x"
        else:
            return f"{explain_part}\n\n🤖 Nahi CALL mat lo {100-chance}% hi chance upar ka 📉\nReason: {reason_txt}"
    if is_put:
        if final=="PUT":
            return f"{explain_part}\n\n🤖 Haan PUT le sakte ho {chance}% NICHE 📉\nReason: {reason_txt}"
        else:
            return f"{explain_part}\n\n🤖 Nahi PUT mat lo Market {actual} hai"
    return f"{explain_part}\n\n🤖 SMART: {final} {chance}% | {reason_txt} | RSI {round(rsi,0)} | Vol {round(vol_ratio,2)}x"

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
    avg_y=cr['avg_y']
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
    msg="📊 <b>CRUDE TOTAL STATUS v17.7 CLEAN</b>\n\n"
    msg=msg+f"1. CURRENT: {curr_tag}\nLive: ${round(live,2)} | ₹{live_inr}\nOpen: ${round(open_p,2)} | ₹{open_inr} | Prev: ${round(prev,2)}\n📊 Vol: Today {int(vol/1000)}K | Avg {int(vol_avg/1000)}K | {round(vol_ratio,2)}x\n\n"
    msg=msg+f"2. LAST 1 HOUR: {h1_ch}% {trend_1m}\n${round(h1_from,2)} -> ${round(live,2)}\nVol 1H: {int(vol_1h/1000)}K Ch: {round(vol_1h_ch,1)}%\n\n"
    msg=msg+f"3. KAL KA: H:${round(high_y,2)} L:${round(low_y,2)} Avg:${round(avg_y,2)}\n\n"
    msg=msg+f"4. WEEK TREND: {week_tag} {week_ch}%\n\n"
    msg=msg+f"5. ⚡ FREE INDICATORS (1-Min):\nEMA 9: ${ema9} | 21: ${ema21} => {ema_cross}\nRSI: {rsi}\n5-Min Momentum: {mom_5m}%\n\n"
    msg=msg+f"6. {vol_pred}\n\n7. {smart_ai}\n\n8. 🗞️ NEWS: {title}\n{imp}\n🔗 <a href=\"{link}\">Full News Padho</a>"
    return msg

@bot.message_handler(func=lambda m: m.text and ('@patialagrvbot' in m.text.lower()))
def mention_h(m):
    user_q=m.text.lower().replace('@patialagrvbot','').strip()
    if not user_q:
        user_q="kya karu"
    cr=get_prices().get('CL=F',{})
    smart=get_smart_ai(LAST_NEWS['title'], LAST_NEWS['imp'], cr, user_q)
    volp=get_volume_prediction(cr)
    reply=f"💬 Tune pucha: {m.text}\n\n{smart}\n\n{volp}"
    kb=InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("📈 CALL lu?",callback_data="ask_call"),InlineKeyboardButton("📉 PUT lu?",callback_data="ask_put"))
    bot.send_message(m.chat.id, reply, parse_mode='HTML', reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hello','crude','hi crude','status'])
def hi_h(m):
    bot.send_message(m.chat.id, build_total_status(), disable_web_page_preview=False)

@bot.message_handler(commands=['liveon','live'])
def liveon(m):
    try:
        bot.send_message(int(GROUP_ID), "LIVE v17.7 CLEAN ✅\n"+build_total_status(), disable_web_page_preview=False)
    except:
        pass
    bot.reply_to(m, 'LIVE ON v17.7 ✅')

@bot.callback_query_handler(func=lambda call: call.data.startswith('ask_'))
def callback_ask(call):
    cr=get_prices().get('CL=F',{})
    bot.answer_callback_query(call.id)
    if 'call' in call.data:
        bot.send_message(call.message.chat.id, get_smart_ai(LAST_NEWS['title'], "call pucha", cr, "call lu?"))
    elif 'put' in call.data:
        bot.send_message(call.message.chat.id, get_smart_ai(LAST_NEWS['title'], "put pucha", cr, "put lu?"))

def update_news_cache():
    try:
        import feedparser
        url='https://news.google.com/rss/search?q=crude+oil+WTI+Brent+-gold+-silver+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=8)
        feed=feedparser.parse(r.content)
        for e in feed.entries:
            clean=e.title.split(' - ')[0].strip()
            low=clean.lower()
            if 'gold' in low or 'silver' in low:
                continue
            if clean in LAST:
                continue
            imp='SIDEWAY 50%'
            emergency=False
            if 'war' in low or 'attack' in low or 'cut' in low:
                imp='BULLISH 🔼 70% upar'
                emergency=True
            elif 'down' in low or 'fall' in low:
                imp='BEARISH 🔻 70% niche'
                emergency=False
            LAST.add(clean)
            LAST_NEWS['title']=clean
            LAST_NEWS['imp']=imp
            LAST_NEWS['link']=e.link
            return emergency,clean,imp,e.link
        return False,None,None,None
    except:
        return False,None,None,None

def updater():
    last_total=0
    last_emer=0
    while True:
        time.sleep(60)
        t=time.time()
        if t-last_emer>=300:
            try:
                is_emer,title,imp,link=update_news_cache()
                if is_emer and title:
                    cr=get_prices().get('CL=F',{'price':91.85})
                    smart=get_smart_ai(title,imp,cr)
                    volp=get_volume_prediction(cr)
                    full=f"🚨 <b>BREAKING</b> 🚨\n⚠️ {title}\n\n{imp}\n\n{volp}\n\n{smart}"
                    bot.send_message(int(GROUP_ID), full, parse_mode='HTML', disable_web_page_preview=False)
            except:
                pass
            last_emer=t
        if t-last_total>=900:
            try:
                bot.send_message(int(GROUP_ID), build_total_status(), disable_web_page_preview=False)
            except:
                pass
            last_total=t

threading.Thread(target=updater, daemon=True).start()
print('Bot v17.7 CLEAN LIVE')
while True:
    try:
        bot.infinity_polling(none_stop=True, timeout=90)
    except Exception as e:
        print("poll err",e)
        time.sleep(10)
