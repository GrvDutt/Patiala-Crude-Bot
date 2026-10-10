# -*- coding: utf-8 -*-
# Main.py v16.3 FINAL - PRICE + GROWTH ALERT with + / - SIGN
import os, threading, time, requests, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v16.3 FINAL + - ALERT')
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
        for sym in ['^NSEI','USO']:
            try:
                h = yf.Ticker(sym).history(period='5d')
                if h.empty:
                    continue
                c = float(h['Close'].iloc[-1])
                p2 = float(h['Close'].iloc[-2])
                ch = (c-p2)/p2*100 if p2 else 0
                v1 = float(h['Volume'].iloc[-1])
                v2 = float(h['Volume'].tail(5).mean())
                prices[sym] = {}
                prices[sym]['price'] = c
                prices[sym]['change'] = ch
                prices[sym]['vol'] = v1
                prices[sym]['vavg'] = v2
            except:
                continue
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
    p = get_prices()
    cr = p.get('CL=F',{'price':91.85,'change':0})
    uso = p.get('USO',{'vol':0,'vavg':1})
    vol = uso['vol']
    vavg = uso['vavg']
    whale = "Shark: No big volume"
    try:
        pct = int(vol / vavg * 100) if vavg else 0
        if vol > vavg * 1.5:
            vml = round(vol/1e6,1)
            whale = "BIG SHARK LIVE "+str(vml)+"M ("+str(pct)+"%)"
    except:
        pass
    price = round(cr['price'],2)
    ch = round(cr['change'],2)
    txt = "F&O SCALP\n"+whale+"\n"
    txt += "Crude: $"+str(price)+" ("+str(ch)+"%)"
    bot.send_message(m.chat.id, txt)

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
        if 'growth' in txt or 'hour' in txt or '%' in txt:
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
        else:
            if a_type == 'growth' and target < 0.2:
                op = '>'
            else:
                op = '>'
        ALERTS.append({'type':a_type,'price':target,'op':op,'chat':m.chat.id,'user':m.from_user.first_name})
        if a_type == 'growth':
            if op == '>':
                bot.reply_to(m, f"✅ GROWTH ALERT SET: +{target}% \nAbhi {round(CACHE['prices'].get('CL=F',{}).get('h1_ch',0.15),2)}% hai, +{target}% hote hi bajega 🚀")
            else:
                bot.reply_to(m, f"✅ GROWTH ALERT SET: -{target}% \nAbhi {round(CACHE['prices'].get('CL=F',{}).get('h1_ch',0.15),2)}% hai, {target}% se niche aate hi bajega 📉")
        else:
            bot.reply_to(m, f"✅ PRICE ALERT SET: Crude {op} ${target} 🚨")
    except Exception as e:
        print(e)
        bot.reply_to(m, "Format: alert when growth +0.30")

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['alerts','my alerts'])
def alert_list_h(m):
    if not ALERT
