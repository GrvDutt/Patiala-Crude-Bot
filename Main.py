# -*- coding: utf-8 -*-
# Main.py v16.3.1 FINAL FIXED - No SyntaxError
import os, threading, time, requests, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v16.3.1 FIXED')
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self,*a):
        pass

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
CACHE = {'prices':{}, 'time':0, 'inr':88.5}
LAST = set()
LAST_NEWS = {'title':'Panic jaisa mahol','imp':'BULLISH 🔼 70% upar - OPEC cut','link':'https://news.google.com/search?q=crude+oil'}
ALERTS = []

def get_inr():
    try:
        import yfinance as yf
        h = yf.Ticker('USDINR=X').history(period='1d')
        if not h.empty:
            return float(h['Close'].iloc[-1])
    except:
        pass
    return CACHE['inr']

def get_prices():
    now = time.time()
    if now - CACHE['time'] < 120 and CACHE['prices']:
        return CACHE['prices']
    prices = {}
    inr = get_inr()
    CACHE['inr'] = inr
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
            week_ch = (live - float(h5['Close'].iloc[0]))/float(h5['Close'].iloc[0])*100 if len(h5)>0 else 0
            h1_from = live
            h1_ch = 0
            if not h1d.empty and len(h1d)>=2:
                h1_from = float(h1d['Close'].iloc[-2])
                h1_ch = (live - h1_from)/h1_from*100 if h1_from else 0
            prices['CL=F'] = {}
            prices['CL=F']['price'] = live
            prices['CL=F']['change'] = (live-prev)/prev*100 if prev else 0
            prices['CL=F']['open'] = open_p
            prices['CL=F']['prev'] = prev
            prices['CL=F']['high_y'] = high_y
            prices['CL=F']['low_y'] = low_y
            prices['CL=F']['avg_y'] = avg_y
            prices['CL=F']['week_ch'] = week_ch
            prices['CL=F']['h1_ch'] = h1_ch
            prices['CL=F']['h1_from'] = h1_from
            prices['CL=F']['inr'] = inr
    except Exception as e:
        print("price err",e)
    if prices:
        CACHE['prices'] = prices
        CACHE['time'] = now
    return prices if prices else CACHE['prices']

def update_news_cache():
    try:
        import feedparser
        url = 'https://news.google.com/rss/search?q=crude+oil+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=8)
        feed = feedparser.parse(r.content)
        for e in feed.entries:
            clean = e.title.split(' - ')[0].strip()
            if clean in LAST:
                continue
            low = clean.lower()
            if 'war' in low or 'attack' in low or 'cut' in low or 'crisis' in low:
                imp = 'BULLISH 🔼 70% upar - OPEC cut'
                emergency = True
            elif 'down' in low or 'fall' in low:
                imp = 'BEARISH 🔻 70% niche'
                emergency = False
            else:
                imp = 'SIDEWAY 50% - '+clean[:50]
                emergency = False
            LAST.add(clean)
            if len(LAST)>100:
                LAST.clear()
            LAST_NEWS['title'] = clean
            LAST_NEWS['imp'] = imp
            LAST_NEWS['link'] = e.link
            return emergency, clean, imp, e.link
        return False, None, None, None
    except Exception as ex:
        print("news err",ex)
        return False, None, None, None

def build_total_status():
    p = get_prices()
    cr = p.get('CL=F')
    if not cr:
        return "📊 <b>CRUDE TOTAL STATUS</b>\n\nBot LIVE ✅"
    title = LAST_NEWS['title']
    imp = LAST_NEWS['imp']
    link = LAST_NEWS['link']
    live = cr['price']
    inr = cr['inr']
    live_inr = int(live*inr)
    open_p = cr['open']
    open_inr = int(open_p*inr)
    prev = cr['prev']
    prev_inr = int(prev*inr)
    h1_ch = round(cr['h1_ch'],2)
    h1_from = cr['h1_from']
    h1_inr = int(h1_from*inr)
    high_y = cr['high_y']
    low_y = cr['low_y']
    avg_y = cr['avg_y']
    high_inr = int(high_y*inr)
    low_inr = int(low_y*inr)
    avg_inr = int(avg_y*inr)
    week_ch = round(cr['week_ch'],2)
    curr_tag = "BULLISH 🟢🔼" if live>prev else "BEARISH 🔴🔻"
    week_tag = "BULLISH 🚀" if week_ch>0 else "BEARISH 📉"
    t1 = "📊 <b>CRUDE TOTAL STATUS</b>\n\n"
    t2 = "1. CURRENT: "+curr_tag+"\n"
    t3 = "Live: $"+str(round(live,2))+" | ₹"+str(live_inr)+"\n"
    t4 = "Open: $"+str(round(open_p,2))+" | ₹"+str(open_inr)+"\n"
    t5 = "Prev: $"+str(round(prev,2))+" | ₹"+str(prev_inr)+"\n\n"
    t6 = "2. LAST 1 HOUR: "+str(h1_ch)+"%\n"
    t6 += "$"+str(round(h1_from,2))+" | ₹"+str(h1_inr)+" -> $"+str(round(live,2))+" | ₹"+str(live_inr)+"\n\n"
    t7 = "3. KAL KA: H:$"+str(round(high_y,2))+" | ₹"+str(high_inr)+" "
    t7 += "L:$"+str(round(low_y,2))+" | ₹"+str(low_inr)+"\n"
    t8 = "Avg:$"+str(round(avg_y,2))+" | ₹"+str(avg_inr)+"\n\n"
    t9 = "4. WEEK TREND: "+week_tag+" "+str(week_ch)+"%\n\n"
    t10 = "5. 🗞️ NEWS:\n⚠️ "+title+"\n"+imp+"\n\n"
    t11 = "🔗 <a href=\""+link+"\">Full News Padho</a>"
    return t1+t2+t3+t4+t5+t6+t7+t8+t9+t10+t11

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip()=='news')
def news_h(m):
    bot.send_message(m.chat.id, "🗞️ News ab <b>hi crude</b> me hi aati hai", parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hello','crude','hi crude'])
def hi_h(m):
    txt = build_total_status()
    bot.send_message(m.chat.id, txt, disable_web_page_preview=False)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['stock','fno'])
def stock_h(m):
    bot.send_message(m.chat.id, "F&O SCALP\nShark: No big volume\nCrude: $91.85 (0%)")

@bot.message_handler(func=lambda m: m.text and 'alert' in m.text.lower() and 'when' in m.text.lower())
def alert_h(m):
    try:
        txt = m.text.lower()
        nums = re.findall(r'[+-]?\d+\.?\d*', txt)
        if not nums:
            bot.reply_to(m, "Use:\nalert when growth +0.30\nor\nalert when growth -0.10")
            return
        raw = nums[-1]
        target = float(raw)
        if 'growth' in txt or '%' in txt:
            a_type = 'growth'
        else:
            a_type = 'price'
        op = '>'
        if raw.startswith('-') or '<' in txt:
            op = '<'
            target = abs(target)
        elif raw.startswith('+') or '>' in txt:
            op = '>'
            target = abs(target)
        ALERTS.append({'type':a_type,'price':target,'op':op,'chat':m.chat.id,'user':m.from_user.first_name})
        if a_type == 'growth':
            if op == '>':
                bot.reply_to(m, f"✅ GROWTH ALERT SET: +{target}% 🚀")
            else:
                bot.reply_to(m, f"✅ GROWTH ALERT SET: -{target}% 📉")
        else:
            bot.reply_to(m, f"✅ PRICE ALERT SET: Crude {op} ${target} 🚨")
    except Exception as e:
        print(e)
        bot.reply_to(m, "Format: alert when growth +0.30")

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['alerts','my alerts'])
def alert_list_h(m):
    if not ALERTS:
        bot.reply_to(m, "Koi alert nahi")
        return
    msg = "📋 ACTIVE ALERTS:\n"
    for i, a in enumerate(ALERTS,1):
        sign = '+' if a['op']=='>' else '-'
        msg += f"{i}. {a['type']} {sign}{a['price']}\n"
    bot.send_message(m.chat.id, msg)

@bot.message_handler(commands=['liveon','live'])
def liveon(m):
    try:
        bot.send_message(int(GROUP_ID), "LIVE v16.3.1 ✅\n"+build_total_status(), disable_web_page_preview=False)
    except:
        pass
    bot.reply_to(m, 'LIVE ON v16.3.1 ✅')

def check_alerts():
    while True:
        time.sleep(90)
        try:
            if not ALERTS:
                continue
            p = get_prices()
            cr = p.get('CL=F')
            if not cr:
                continue
            live = float(cr['price'])
            growth = float(cr['h1_ch'])
            for a in ALERTS[:]:
                hit = False
                if a['type'] == 'price':
                    if a['op'] == '>' and live >= a['price']:
                        hit = True
                    elif a['op'] == '<' and live <= a['price']:
                        hit = True
                else:
                    if a['op'] == '>' and growth >= a['price']:
                        hit = True
                    elif a['op'] == '<' and growth <= a['price']:
                        hit = True
                if hit:
                    if a['type']=='price':
                        msg = f"🚨 <b>PRICE ALERT HIT</b> 🚨\nLive: ${round(live,2)}\nBy: {a['user']}"
                    else:
                        sign = '+' if a['op']=='>' else '-'
                        msg = f"🚨 <b>GROWTH ALERT HIT {sign}{a['price']}%</b> 🚨\nAbhi: {round(growth,2)}%\nLive: ${round(live,2)}"
                    try:
                        bot.send_message(a['chat'], msg)
                        bot.send_message(int(GROUP_ID), msg)
                    except:
                        pass
                    ALERTS.remove(a)
        except Exception as e:
            print("alert err",e)

def updater():
    last_total = 0
    last_emer = 0
    while True:
        time.sleep(60)
        t = time.time()
        if t - last_emer >= 300:
            try:
                is_emer, title, imp, link = update_news_cache()
                if is_emer and title:
                    p = get_prices()
                    cr = p.get('CL=F',{'price':91.85})['price']
                    msg = "🚨 <b>BREAKING EMERGENCY</b> 🚨\n\n⚠️ "+title+"\n\n💥 "+imp+"\nCrude: $"+str(round(cr,2))
                    bot.send_message(int(GROUP_ID), msg, disable_web_page_preview=False)
            except:
                pass
            last_emer = t
        if t - last_total >= 900:
            try:
                txt = build_total_status()
                bot.send_message(int(GROUP_ID), txt, disable_web_page_preview=False)
            except:
                pass
            last_total = t

threading.Thread(target=check_alerts, daemon=True).start()
threading.Thread(target=updater, daemon=True).start()
print('Bot v16.3.1 LIVE')
while True:
    try:
        bot.infinity_polling(none_stop=True, timeout=90)
    except Exception as e:
        print("poll err",e)
        time.sleep(10)
