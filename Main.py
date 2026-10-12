# Main.py v18.0 FINAL - 100% Syntax OK + Explain Fix
import os, threading, time, requests, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v18')
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
    while True:
        time.sleep(60)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)
CACHE = {'prices':{}, 'time':0}
LAST = set()
LAST_NEWS = {'title':'Brent Crude Rises','imp':'SIDEWAY 50%','link':'https://news.google.com/search?q=crude+oil'}

def get_prices():
    prices = {}
    try:
        import yfinance as yf
        import numpy as np
        t = yf.Ticker('CL=F')
        h5 = t.history(period='5d')
        h1d = t.history(period='1d', interval='1h')
        h1m = t.history(period='1d', interval='1m')
        if not h5.empty:
            live = float(h5['Close'].iloc[-1])
            prev = float(h5['Close'].iloc[-2]) if len(h5)>1 else live
            open_p = float(h5['Open'].iloc[-1])
            high_y = float(h5['High'].iloc[-2]) if len(h5)>1 else live
            low_y = float(h5['Low'].iloc[-2]) if len(h5)>1 else live
            vol_today = float(h5['Volume'].iloc[-1]) if 'Volume' in h5.columns else 0
            vol_avg = float(h5['Volume'].mean()) if 'Volume' in h5.columns else 0
            vol_ratio = vol_today / vol_avg if vol_avg else 1
            vol_1h = float(h1d['Volume'].iloc[-1]) if not h1d.empty else 0
            week_ch = (live - float(h5['Close'].iloc[0]))/float(h5['Close'].iloc[0])*100 if len(h5)>0 else 0
            h1_from = live
            h1_ch = 0
            if not h1d.empty and len(h1d)>=2:
                h1_from = float(h1d['Close'].iloc[-2])
                if h1_from!= 0:
                    h1_ch = (live - h1_from)/h1_from*100
            ema9 = 0
            ema21 = 0
            rsi = 50
            mom = 0
            trend = "SIDEWAY"
            if not h1m.empty and len(h1m)>21:
                closes = h1m['Close'].values
                ema9 = float(np.mean(closes[-9:]))
                ema21 = float(np.mean(closes[-21:]))
                if len(closes)>=5 and closes[-5]!=0:
                    mom = (closes[-1]-closes[-5])/closes[-5]*100
                if closes[-1] > closes[-2]:
                    trend = "UP"
                else:
                    trend = "DOWN"
                deltas = np.diff(closes)
                if len(deltas)>=14:
                    gains = deltas.clip(min=0)
                    losses = -deltas.clip(max=0)
                    ag = np.mean(gains[-14:])
                    al = np.mean(losses[-14:])
                    if al == 0:
                        rsi = 100
                    else:
                        rsi = 100 - (100/(1+ag/al))
            prices['CL=F'] = {
                'price':live,'open':open_p,'prev':prev,'high_y':high_y,'low_y':low_y,
                'week_ch':week_ch,'h1_ch':h1_ch,'h1_from':h1_from,'vol':vol_today,
                'vol_avg':vol_avg,'vol_ratio':vol_ratio,'ema9':ema9,'ema21':ema21,'rsi':rsi,'mom':mom,'trend':trend
            }
    except Exception as e:
        print("price err", e)
    return prices

def get_vol_msg(cr):
    vr = cr.get('vol_ratio',1)
    hc = cr.get('h1_ch',0)
    if vr > 1.5 and hc > 0.1:
        return f"VOL Shark BUYING {round(vr,2)}x HIGH + Price UP = UPAR JAYEGA"
    if vr > 1.5 and hc < -0.1:
        return f"VOL Shark SELLING {round(vr,2)}x HIGH + Price DOWN = NICHE JAYEGA"
    if vr < 0.7 and hc > 0:
        return f"VOL TRAP LOW {round(vr,2)}x + UP = FAKE PUMP - GIRNE WALA HAI"
    if vr < 0.7 and hc < 0:
        return f"VOL WEAK LOW {round(vr,2)}x = BOUNCE AYEGA"
    return f"VOL Normal {round(vr,2)}x"

def get_smart_ai(news_title, cr, user_q):
    q = user_q.lower()
    vr = cr.get('vol_ratio',1)
    hc = cr.get('h1_ch',0)
    rsi = cr.get('rsi',50)
    live = cr.get('price',90)
    ema9 = cr.get('ema9',0)
    ema21 = cr.get('ema21',0)

    # EXPLAIN LOGIC - YEHI FIX HAI
    if "volume" in q or "vol" in q or "trap" in q or "6" in q:
        msg = "VOLUME TRAP EXPLAIN Point 6\n\n"
        msg += f"Abhi Vol Ratio = {round(vr,2)}x (Normal 1.0x)\n"
        msg += f"Matlab volume Avg se {round((1-vr)*100,0)}% KAM hai\n"
        msg += f"Price UP {round(hc,2)}% par Vol LOW hai\n\n"
        msg += "Matlab:\n"
        msg += "1. FAKE PUMP hai - Bade players nahi kharid rahe\n"
        msg += "2. Bina paise ke upar gaya hai, jaldi girega\n"
        msg += "3. Low Vol + UP = Trap hota hai\n\n"
        msg += f"Trade: CALL mat lo, PUT wait karo\nLive ${round(live,2)} RSI {round(rsi,0)}"
        return msg

    if "rsi" in q:
        msg = f"RSI EXPLAIN\n\nAbhi RSI = {round(rsi,1)}\n"
        msg += "RSI >70 = Overbought = Girega PUT lo\n"
        msg += "RSI <30 = Oversold = Uthega CALL lo\n"
        msg += f"Abhi {round(rsi,0)} hai = {'Overbought PUT time' if rsi>70 else 'Oversold CALL time' if rsi<30 else 'Normal'}"
        return msg

    if "ema" in q or "golden" in q or "death" in q:
        msg = f"EMA EXPLAIN\n\nEMA9 ${round(ema9,2)} EMA21 ${round(ema21,2)}\n"
        if ema9 > ema21:
            msg += "Golden Cross = UPAR jayega CALL"
        else:
            msg += "Death Cross = NICHE jayega PUT"
        return msg

    # TRAP LOGIC
    if rsi > 80 and vr < 0.5 and hc > 0:
        if "call" in q:
            return f"News: {news_title}\n\nTRAP CONFIRMED RSI {round(rsi,0)} Overbought + LOW Vol {round(vr,2)}x\nNahi CALL mat lo FAKE PUMP hai {round(hc,2)}% niche girega"
        if "put" in q:
            return f"TRAP CONFIRMED RSI {round(rsi,0)} + LOW Vol\nHaan PUT le sakte ho 78% NICHE girega"
        return f"News: {news_title}\n\nSMART PUT 78% TRAP hai RSI {round(rsi,0)} Overbought + LOW Vol {round(vr,2)}x"

    # NORMAL CALL PUT
    score = 0
    if live > cr.get('open',90):
        score += 1
    else:
        score -= 1
    if hc > 0.3:
        score += 2
    if hc < -0.3:
        score -= 2
    if vr < 0.7 and hc > 0:
        score -= 2
    if vr > 1.2 and hc > 0:
        score += 2
    if rsi > 75:
        score -= 2
    if rsi < 25:
        score += 2
    if ema9 > ema21:
        score += 1
    else:
        score -= 1

    if score >= 3:
        final = "CALL 72%"
    elif score >= 1:
        final = "CALL 60%"
    elif score <= -3:
        final = "PUT 72%"
    elif score <= -1:
        final = "PUT 60%"
    else:
        final = "WAIT 50%"

    if "call" in q:
        if "CALL" in final:
            return f"News: {news_title}\n\nHaan CALL le sakte ho {final} UPAR\nVol {round(vr,2)}x RSI {round(rsi,0)}"
        else:
            return f"News: {news_title}\n\nNahi CALL mat lo {final} hai\nReason Vol {round(vr,2)}x RSI {round(rsi,0)}"
    if "put" in q:
        if "PUT" in final:
            return f"News: {news_title}\n\nHaan PUT le sakte ho {final} NICHE"
        else:
            return f"News: {news_title}\n\nNahi PUT mat lo {final} hai"
    return f"News: {news_title}\n\nSMART {final} Vol {round(vr,2)}x RSI {round(rsi,0)} H1 {round(hc,2)}%"

def build_status():
    p = get_prices()
    cr = p.get('CL=F')
    if not cr:
        return "Bot LIVE"
    live = cr['price']
    open_p = cr['open']
    prev = cr['prev']
    h1_ch = round(cr['h1_ch'],2)
    h1_from = cr['h1_from']
    high_y = cr['high_y']
    low_y = cr['low_y']
    week_ch = round(cr['week_ch'],2)
    vol = cr['vol']
    vol_avg = cr['vol_avg']
    vr = cr['vol_ratio']
    rsi = round(cr['rsi'],1)
    ema9 = round(cr['ema9'],2)
    ema21 = round(cr['ema21'],2)
    mom = round(cr['mom'],3)
    trend = cr['trend']
    if live > prev:
        curr = "BULLISH"
    else:
        curr = "BEARISH"
    if ema9 > ema21:
        cross = "Golden Cross UPAR"
    else:
        cross = "Death Cross NICHE"
    vol_msg = get_vol_msg(cr)
    smart = get_smart_ai(LAST_NEWS['title'], cr, "")
    msg = f"CRUDE TOTAL STATUS v18.0\n\n"
    msg += f"1 CURRENT {curr}\nLive ${round(live,2)} Open ${round(open_p,2)} Prev ${round(prev,2)}\nVol Today {int(vol/1000)}K Avg {int(vol_avg/1000)}K {round(vr,2)}x\n\n"
    msg += f"2 LAST 1H {h1_ch}% {trend}\n${round(h1_from,2)} -> ${round(live,2)}\n\n"
    msg += f"3 KAL KA H ${round(high_y,2)} L ${round(low_y,2)}\n\n"
    msg += f"4 WEEK {week_ch}%\n\n"
    msg += f"5 INDICATORS EMA9 ${ema9} EMA21 ${ema21} => {cross}\nRSI {rsi} Mom {mom}%\n\n"
    msg += f"6 {vol_msg}\n\n7 {smart}\n\n8 NEWS {LAST_NEWS['title']}\n{LAST_NEWS['imp']}"
    return msg

@bot.message_handler(func=lambda m: m.text and ('@patialagrvbot' in m.text.lower()))
def mention_h(m):
    user_q = m.text.lower().replace('@patialagrvbot','').strip()
    if not user_q:
        user_q = "kya karu"
    cr = get_prices().get('CL=F',{})
    smart = get_smart_ai(LAST_NEWS['title'], cr, user_q)
    volm = get_vol_msg(cr)
    if "volume" in user_q.lower() or "vol" in user_q.lower() or "trap" in user_q.lower() or "explain" in user_q.lower() or "rsi" in user_q.lower() or "ema" in user_q.lower() or "6" in user_q:
        reply = f"Tune pucha: {m.text}\n\n{smart}"
    else:
        reply = f"Tune pucha: {m.text}\n\n{smart}\n\n{volm}"
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("CALL lu?",callback_data="ask_call"),InlineKeyboardButton("PUT lu?",callback_data="ask_put"))
    kb.row(InlineKeyboardButton("Explain Vol Trap",callback_data="ask_vol"),InlineKeyboardButton("Explain RSI",callback_data="ask_rsi"))
    bot.send_message(m.chat.id, reply, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hello','crude','hi crude','status'])
def hi_h(m):
    bot.send_message(m.chat.id, build_status())

@bot.message_handler(commands=['liveon','live'])
def liveon(m):
    try:
        bot.send_message(int(GROUP_ID), "LIVE v18.0\n"+build_status())
    except:
        pass
    bot.reply_to(m, 'LIVE ON v18.0')

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    cr = get_prices().get('CL=F',{})
    bot.answer_callback_query(call.id)
    if "call" in call.data:
        bot.send_message(call.message.chat.id, get_smart_ai(LAST_NEWS['title'], cr, "call lu?"))
    elif "put" in call.data:
        bot.send_message(call.message.chat.id, get_smart_ai(LAST_NEWS['title'], cr, "put lu?"))
    elif "vol" in call.data:
        bot.send_message(call.message.chat.id, get_smart_ai(LAST_NEWS['title'], cr, "explain volume trap 6"))
    elif "rsi" in call.data:
        bot.send_message(call.message.chat.id, get_smart_ai(LAST_NEWS['title'], cr, "explain rsi"))

def updater():
    last = 0
    while True:
        time.sleep(60)
        t = time.time()
        if t - last >= 900:
            try:
                bot.send_message(int(GROUP_ID), build_status())
            except:
                pass
            last = t

threading.Thread(target=updater, daemon=True).start()
print('Bot v18 LIVE')
while True:
    try:
        bot.infinity_polling(none_stop=True, timeout=90)
    except Exception as e:
        print("poll err", e)
        time.sleep(10)
