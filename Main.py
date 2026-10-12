# -*- coding: utf-8 -*-
# Main.py v16.7 FINAL FIX - Conversation Proper
import os, threading, time, requests, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v16.7 CONVERSATION FIX')
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
        return {'USA (NYSE/NASDAQ)':is_open(et,9,30,16,0),'INDIA (NSE)':is_open(ist,9,15,15,30),'UK (LSE)':False,'JAPAN (Nikkei)':False,'MCX (CRUDE)':is_open(ist,9,0,23,30),'times':{'ET':et.strftime('%I:%M %p'),'IST':ist.strftime('%I:%M %p')}}
    except: return {'USA (NYSE/NASDAQ)':False,'INDIA (NSE)':True,'times':{}}

def get_global_markets_data():
    data={}; syms={'USA NASDAQ':'^IXIC','USA S&P500':'^GSPC','USA DOW':'^DJI','INDIA NIFTY':'^NSEI','INDIA SENSEX':'^BSESN','UK FTSE':'^FTSE','JAPAN Nikkei':'^N225'}
    try:
        import yfinance as yf
        for name,sym in syms.items():
            try:
                t=yf.Ticker(sym); h1d=t.history(period='1d'); h1w=t.history(period='5d')
                if not h1d.empty and not h1w.empty:
                    live=float(h1d['Close'].iloc[-1]); day_h=float(h1d['High'].iloc[-1]); day_l=float(h1d['Low'].iloc[-1]); week_h=float(h1w['High'].max()); week_l=float(h1w['Low'].min()); ch=((live - float(h1d['Open'].iloc[-1]))/float(h1d['Open'].iloc[-1])*100) if float(h1d['Open'].iloc[-1]) else 0
                    data[name]={'live':live,'day_h':day_h,'day_l':day_l,'week_h':week_h,'week_l':week_l,'ch':ch}
            except: continue
    except: pass
    return data

def get_ai_suggestion(news_title, news_imp):
    p=get_prices(); cr=p.get('CL=F',{}); vol_ratio=cr.get('vol_ratio',1); h1_ch=cr.get('h1_ch',0); live=cr.get('price',90)
    low=(news_title+" "+news_imp).lower()
    if 'war' in low or 'attack' in low or 'blast' in low or 'iran' in low or 'strike' in low:
        if vol_ratio>1.2 and h1_ch>0: return f"🚀 BULLISH ATTACK NEWS\nVol HIGH {round(vol_ratio,2)}x + Price up {h1_ch}%\n👉 CALL BUY kar sakte ho, SL ${round(live-0.8,2)}"
        else: return f"⚠️ ATTACK NEWS but Vol LOW {round(vol_ratio,2)}x\n👉 WAIT karo 15 min"
    elif 'down' in low or 'fall' in low or 'drop' in low or 'bearish' in low: return f"📉 BEARISH NEWS\n👉 PUT BUY karo"
    else: return f"🤔 Sideways {h1_ch}%\n👉 WAIT karo"

def get_news_keyboard():
    markup=InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📈 CALL karu?",callback_data="ask_call"),InlineKeyboardButton("📉 PUT karu?",callback_data="ask_put"))
    markup.row(InlineKeyboardButton("⏳ WAIT karu?",callback_data="ask_wait"),InlineKeyboardButton("💬 Discuss",callback_data="ask_discuss"))
    return markup

def update_news_cache():
    try:
        import feedparser
        url='https://news.google.com/rss/search?q=crude+oil+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=8)
        feed=feedparser.parse(r.content)
        for e in feed.entries:
            clean=e.title.split(' - ')[0].strip()
            if clean in LAST: continue
            low=clean.lower()
            if 'war' in low or 'attack' in low or 'cut' in low or 'crisis' in low:
                imp='BULLISH 🔼 70% upar - OPEC cut'; emergency=True
            elif 'down' in low or 'fall' in low:
                imp='BEARISH 🔻 70% niche'; emergency=False
            else:
                imp='SIDEWAY 50% - '+clean[:50]; emergency=False
            LAST.add(clean)
            if len(LAST)>100: LAST.clear()
            LAST_NEWS['title']=clean; LAST_NEWS['imp']=imp; LAST_NEWS['link']=e.link
            return emergency,clean,imp,e.link
        return False,None,None,None
    except Exception as ex:
        print("news err",ex); return False,None,None,None

def build_total_status():
    p=get_prices(); cr=p.get('CL=F')
    if not cr: return "📊 <b>CRUDE TOTAL STATUS</b>\n\nBot LIVE ✅"
    title=LAST_NEWS['title']; imp=LAST_NEWS['imp']; link=LAST_NEWS['link']
    live=cr['price']; inr=cr['inr']; live_inr=int(live*inr); open_p=cr['open']; open_inr=int(open_p*inr); prev=cr['prev']; prev_inr=int(prev*inr); h1_ch=round(cr['h1_ch'],2); h1_from=cr['h1_from']; h1_inr=int(h1_from*inr); high_y=cr['high_y']; low_y=cr['low_y']; avg_y=cr['avg_y']; high_inr=int(high_y*inr); low_inr=int(low_y*inr); avg_inr=int(avg_y*inr); week_ch=round(cr['week_ch'],2)
    curr_tag="BULLISH 🟢🔼" if live>prev else "BEARISH 🔴🔻"; week_tag="BULLISH 🚀" if week_ch>0 else "BEARISH 📉"
    vol=cr.get('vol',0); vol_yday=cr.get('vol_yday',0); vol_avg=cr.get('vol_avg',0); vol_ratio=cr.get('vol_ratio',1); vol_change=cr.get('vol_change',0); vol_1h=cr.get('vol_1h',0); vol_1h_prev=cr.get('vol_1h_prev',0); vol_1h_ch=((vol_1h - vol_1h_prev)/vol_1h_prev*100) if vol_1h_prev else 0
    t1="📊 <b>CRUDE TOTAL STATUS</b>\n\n"; t2="1. CURRENT: "+curr_tag+"\n"; t3="Live: $"+str(round(live,2))+" | ₹"+str(live_inr)+"\n"; t4="Open: $"+str(round(open_p,2))+" | ₹"+str(open_inr)+"\n"; t5="Prev: $"+str(round(prev,2))+" | ₹"+str(prev_inr)+"\n"; t5+=f"📊 Vol: Today {int(vol/1000)}K | Avg {int(vol_avg/1000)}K | Change {round(vol_change,1)}% ({round(vol_ratio,2)}x)\n\n"
    t6="2. LAST 1 HOUR: "+str(h1_ch)+"%\n"; t6+="$"+str(round(h1_from,2))+" | ₹"+str(h1_inr)+" -> $"+str(round(live,2))+" | ₹"+str(live_inr)+"\n"; t6+=f"📊 Vol 1H: {int(vol_1h/1000)}K | Prev {int(vol_1h_prev/1000)}K | Change {round(vol_1h_ch,1)}%\n\n"
    t7="3. KAL KA: H:$"+str(round(high_y,2))+" | ₹"+str(high_inr)+" L:$"+str(round(low_y,2))+" | ₹"+str(low_inr)+"\n"; t8="Avg:$"+str(round(avg_y,2))+" | ₹"+str(avg_inr)+"\n"; t8+=f"📊 Vol YDay: {int(vol_yday/1000)}K | Avg {int(vol_avg/1000)}K | Today {int(vol/1000)}K\n\n"
    t9="4. WEEK TREND: "+week_tag+" "+str(week_ch)+"%\n\n"; t10="5. 🗞️ NEWS:\n⚠️ "+title+"\n"+imp+"\n\n"; t11="🔗 <a href=\""+link+"\">Full News Padho</a>"
    return t1+t2+t3+t4+t5+t6+t7+t8+t9+t10+t11

def build_market_status_msg():
    ms=get_market_status(); times=ms.pop('times',{}); gdata=get_global_markets_data()
    msg="🌍 <b>GLOBAL MARKET STATUS - USA TOP</b>\n\n"
    order=['USA NASDAQ','USA S&P500','USA DOW','INDIA NIFTY','INDIA SENSEX','UK FTSE','JAPAN Nikkei']
    for name in order:
        open_status = ms.get('USA (NYSE/NASDAQ)',False) if 'USA' in name else ms.get('INDIA (NSE)',False) if 'INDIA' in name else False
        status_emoji="OPEN 🟢" if open_status else "CLOSE 🔴"
        if name in gdata:
            d=gdata[name]; msg+=f"<b>{'🔹' if 'USA' in name else '▫️'} {name}</b>: {status_emoji}\n Live: {round(d['live'],2)} ({round(d['ch'],2)}%)\n Day: H {round(d['day_h'],2)} L {round(d['day_l'],2)}\n Week: H {round(d['week_h'],2)} L {round(d['week_l'],2)}\n\n"
        else: msg+=f"{'🔹' if 'USA' in name else '▫️'} {name}: {status_emoji}\n\n"
    cr=get_prices().get('CL=F',{})
    if cr: msg+=f"<b>▫️ CRUDE OIL</b>: OPEN 🟢\n Live: ${round(cr['price'],2)}\n Day H ${round(cr['high_y'],2)} L ${round(cr['low_y'],2)}\n\n"
    if times: msg+=f"🕐 ET: {times.get('ET','')} | IST: {times.get('IST','')}"
    return msg

# ====== CONVERSATION HANDLERS - SABSE UPAR RAKHNA ZAROORI HAI ======
@bot.message_handler(func=lambda m: m.text and ('@patialagrvbot' in m.text.lower() or '@patialacrvbot' in m.text.lower()))
def mention_h(m):
    user_q = m.text.lower().replace('@patialagrvbot','').replace('@patialacrvbot','').replace('@patialagrv','').strip()
    if not user_q: user_q = "market kya lag raha hai?"
    p=get_prices(); cr=p.get('CL=F',{}); live=cr.get('price',90.64); h1_ch=round(cr.get('h1_ch',0.29),2); week_ch=round(cr.get('week_ch',2.67),2); open_p=cr.get('open',91.83)

    if 'upar' in user_q or 'bullish' in user_q or 'bad' in user_q or 'tezi' in user_q or 'up' in user_q:
        reply = f"💬 Tu sahi keh raha hai!\n\nTune bola: <b>{m.text}</b>\n\n📈 LAST 1 HOUR: <b>{h1_ch}% UP</b> hai ${round(cr.get('h1_from',90.38),2)} -> ${round(live,2)}\nLekin FULL DAY abhi BEARISH hai kyunki Open ${round(open_p,2)} se niche hai.\n\n👉 Matlab: Intraday BULLISH ✅, Day BEARISH ❌\n\nTera chart wala 8694 breakout isi ka hai. Ab bata PUT lena hai 192 pe ya WAIT?"
    elif 'niche' in user_q or 'bearish' in user_q or 'gir' in user_q or 'down' in user_q:
        reply = f"💬 Haan kal 90.01 tak gira tha, par ab bounce {h1_ch}% ka ho raha hai.\nLive ${round(live,2)} | Week {week_ch}% BULLISH hai\nPUT ka soch raha hai kya?"
    elif 'kya' in user_q or 'lag' in user_q or 'bata' in user_q or 'kaisa' in user_q:
        suggestion=get_ai_suggestion(LAST_NEWS['title'], LAST_NEWS['imp']+" "+user_q)
        reply = f"💬 Puchha: <b>{m.text}</b>\n\n💰 Live ${round(live,2)} | 1H {h1_ch}% | Week {week_ch}%\n🗞️ {LAST_NEWS['title'][:70]}\n\n{suggestion}"
    else:
        suggestion=get_ai_suggestion(LAST_NEWS['title'], LAST_NEWS['imp']+" "+user_q)
        reply = f"💬 Tumne: <b>{m.text}</b>\n\n💰 Live ${round(live,2)} | 1H {h1_ch}%\n\n{suggestion}\n\nAur bolo - CALL lu ya PUT?"
    bot.send_message(m.chat.id, reply, parse_mode='HTML', reply_markup=get_news_keyboard())

@bot.message_handler(func=lambda m: m.text and m.reply_to_message and m.reply_to_message.from_user and m.reply_to_message.from_user.username and 'Patiala' in (m.reply_to_message.from_user.username or ''))
def reply_to_bot_h(m):
    mention_h(m)

# ====== NORMAL COMMANDS - EXACT MATCH ONLY ======
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip()=='news')
def news_h(m): bot.send_message(m.chat.id, "🗞️ News ab <b>hi crude</b> me hi aati hai", parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hello','crude','hi crude'])
def hi_h(m): bot.send_message(m.chat.id, build_total_status(), disable_web_page_preview=False)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['market','markets','global','global market','market status'])
def market_h(m): bot.send_message(m.chat.id, build_market_status_msg(), parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip()=='volume')
def volume_h(m):
    p=get_prices(); cr=p.get('CL=F')
    if not cr: bot.reply_to(m, "Volume nahi mila"); return
    vol=cr.get('vol',0); avg=cr.get('vol_avg',0); ratio=cr.get('vol_ratio',1)
    tag="🔥 HIGH - Shark Active" if ratio>1.5 else "🐟 LOW" if ratio<0.8 else "Normal"
    bot.send_message(m.chat.id, f"📊 <b>VOLUME</b
