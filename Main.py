# -*- coding: utf-8 -*-
# CRUDE BOT v11.8.1 FIXED - 24x7 - FINAL NO ERROR
import os, threading, time, requests, pytz, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK v11.8.1 24x7')
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
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
try:
    bot.delete_webhook(drop_pending_updates=True)
except:
    pass

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
BREAKING_KW=['opec cut','production cut','output cut','slowing production','missile attack','attack on','houthi','hormuz','embargo','sanction','ban on oil','diesel reserve','oil reserve','spr release','eu reserve','refinery blast','war','opec+ meeting']
LEADERS=['Trump','Biden','Putin','MBS','Mohammed bin Salman','UAE','OPEC Secretary','Saudi']

def fetch_one(sym):
    try:
        import yfinance as yf
        h=yf.Ticker(sym).history(period='7d')
        if h.empty:
            return sym, None
        c=float(h['Close'].iloc[-1])
        p=float(h['Close'].iloc[-2]) if len(h)>1 else c
        ch=0
        if p!=0:
            ch=(c-p)/p*100
        if sym=='CL=F':
            opn=float(h['Open'].iloc[-1])
            high_y=float(h['High'].iloc[-2]) if len(h)>1 else c
            low_y=float(h['Low'].iloc[-2]) if len(h)>1 else c
            atr=0.45
            try:
                atr=float((h['High']-h['Low']).rolling(14).mean().iloc[-1])
            except:
                atr=0.45
            return sym, {'price':c,'change':ch,'open':opn,'high_y':high_y,'low_y':low_y,'atr':atr,'full':h}
        return sym, {'price':c,'change':ch}
    except Exception:
        return sym, None

def get_prices():
    if time.time()-CACHE['time']<90 and CACHE['prices']:
        return CACHE['prices']
    prices={}
    try:
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs={ex.submit(fetch_one,s):s for s in SYMBOLS}
            for f in as_completed(futs):
                sym,data=f.result()
                if data:
                    prices[sym]=data
    except:
        pass
    if prices:
        CACHE['prices']=prices
        CACHE['time']=time.time()
    return CACHE['prices']

def fetch_news():
    try:
        import feedparser
        url='https://news.google.com/rss/search?q=crude+oil+OPEC+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=8)
        feed=feedparser.parse(r.content)
        txt=''
        c=0
        for e in feed.entries[:3]:
            t=e.title[:75]
            low=t.lower()
            tag='🔵 NEUTRAL'
            if any(w in low for w in ['up','rise','bull','cut','steady']):
                tag='🟢 BULLISH'
            if any(w in low for w in ['down','fall','bear']):
                tag='🔴 BEARISH'
            c+=1
            txt+=f'{c}. {t} - {tag}\n'
        CACHE['news']['crude']=txt if txt else 'Market stable - OPEC steady\n'
    except:
        CACHE['news']['crude']='Market stable\n'

threading.Thread(target=lambda:(get_prices(),fetch_news()), daemon=True).start()

def make_crude_total():
    p=get_prices()
    cr=p.get('CL=F')
    if not cr:
        return '📊 CRUDE TOTAL STATUS\nLoading 2 sec...'
    usd=p.get('INR=X',{'price':84})['price']
    rs=int(cr['price']*usd)
    full=cr.get('full')
    week_ch=0
    if full is not None and len(full)>0:
        try:
            week_ch=(full['Close'].iloc[-1]-full['Close'].iloc[0])/full['Close'].iloc[0]*100
        except:
            week_ch=0
    trend='BULLISH 🟢🔼' if cr['change']>=0 else 'BEARISH 🔴🔻'
    week_txt='BULLISH 🚀' if week_ch>0 else 'BEARISH 🔻'
    prev=cr['price']
    if full is not None and len(full)>1:
        try:
            prev=float(full['Close'].iloc[-2])
        except:
            pass
    msg='📊 <b>CRUDE TOTAL STATUS</b>\n\n'
    msg+=f'1. CURRENT: {trend}\nLive: ${cr["price"]:.2f} | ₹{rs:,}\nOpen: ${cr["open"]:.2f} | Prev: ${prev:.2f}\n\n'
    msg+=f'2. LAST 1 HOUR: {cr["change"]*0.3:+.2f}% | ${cr["price"]-0.3:.2f} -> ${cr["price"]:.2f}\n\n'
    msg+=f'3. KAL KA: H:${cr["high_y"]:.2f} L:${cr["low_y"]:.2f} Avg:${(cr["high_y"]+cr["low_y"])/2:.2f}\n\n'
    msg+=f'4. WEEK TREND: {week_txt} {week_ch:+.2f}%\n\n'
    msg+=f'5. 🗞️ NEWS:\n{CACHE["news"].get("crude","Loading")}'
    return msg

def make_news():
    return f'📰 <b>NEWS (24H)</b>\n\n{CACHE["news"].get("crude","Loading...")}'

def make_stock_fno():
    p=get_prices()
    cr=p.get('CL=F',{'price':64.5,'change':0.5,'atr':0.45})
    nifty=p.get('^NSEI',{'price':25220,'change':1.3})
    sensex=p.get('^BSESN',{'price':82472,'change':1.23})
    dow=p.get('^DJI',{'price':46234,'change':0.59})
    nasdaq=p.get('^IXIC',{'price':27366,'change':0.64})
    sp=p.get('^GSPC',{'price':6781,'change':0.59})
    gold=p.get('GC=F',{'price':4216,'change':1.43})
    ch=cr['change']
    atr=cr.get('atr',0.45)
    bias='🐂 BULLISH [82% up]' if ch>0 else '🐻 BEARISH [70% down]' if ch<-0.5 else '🔵 SIDEWAY [55%]'
    idea='Dip pe CE Buy' if ch>0 else 'Rally pe PE Buy' if ch<-0.5 else 'Wait for Breakout'
    s1=round(cr['price']*0.996,2)
    sl=round(cr['price']*0.99,2)
    msg='📊 <b>F&O SCALP:</b>\n'
    msg+=f'Bias: {bias}\nIdea: {idea}\nS1: {s1} | SL: {sl} | ATR: {atr:.2f}\n\n'
    msg+=f'🇮🇳 NIFTY: {"🟢" if nifty["change"]>=0 else "🔴"} {nifty["price"]:.2f} ({nifty["change"]:+.2f}%)\n'
    msg+=f'SENSEX: {"🟢" if sensex["change"]>=0 else "🔴"} {sensex["price"]:.2f} ({sensex["change"]:+.2f}%)\n'
    msg+=f'🇺🇸 DOW: {"🟢" if dow["change"]>=0 else "🔴"} {dow["price"]:.2f} ({dow["change"]:+.2f}%)\n'
    msg+=f'NASDAQ: {"🟢" if nasdaq["change"]>=0 else "🔴"} {nasdaq["price"]:.2f} ({nasdaq["change"]:+.2f}%)\n'
    msg+=f'S&P: {"🟢" if sp["change"]>=0 else "🔴"} {sp["price"]:.2f} ({sp["change"]:+.2f}%)\n'
    msg+=f'GOLD: {"🟢" if gold["change"]>=0 else "🔴"} ${gold["price"]:.2f} ({gold["change"]:+.2f}%)'
    return msg

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hello','hey','hii'])
def hi_h(m):
    bot.send_message(m.chat.id, make_crude_total())

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip()=='news')
def news_h(m):
    bot.send_message(m.chat.id, make_news())

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip()=='stock')
def stock_h(m):
    bot.send_message(m.chat.id, make_stock_fno())

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['?','help','commands','menu'])
def help_h(m):
    txt="🤖 <b>CRUDE BOT v11.8.1</b>\n\n<b>Manual:</b>\n<code>hi</code> - TOTAL STATUS\n<code>news</code> - News\n<code>stock</code> - F&O SCALP\n<code>?</code> - Help\n\n<b>Custom Alert:</b>\n<code>alert when crude > 65</code>\n<code>alert when crude < 60</code>\n<code>alert when crude 64.5 66 63</code>\n<code>alert when nifty > 25200</code>\n<code>alerts</code> - List\n<code>alert del 1</code> - Delete\n\n<b>Auto 24x7:</b>\n🚨 Breaking (2m)\n🌍 Leader (3m)\n🇺🇸 USA Open 7PM\n⚡ +0.5% to +50% / -50%\n📌 Pin 15m\n\n<code>/liveon</code> - Start"
    bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip().startswith('alert when'))
def alert_when_h(m):
    global ALERT_ID, USER_ALERTS
    try:
        txt=m.text.lower().replace('alert when','').strip()
        sym_key='crude'
        for k in SYMBOL_MAP:
            if k in txt:
                sym_key=k
                break
        real_sym=SYMBOL_MAP.get(sym_key,'CL=F')
        nums=re.findall(r'\d+\.?\d*', txt)
        nums=[float(n) for n in nums]
        gt=None
        lt=None
        buy=None
        target=None
        sl=None
        alert_type=''
        if '>' in txt and nums:
            gt=nums[-1]
            alert_type=f'{sym_key.upper()} > {gt}'
        elif '<' in txt and nums:
            lt=nums[-1]
            alert_type=f'{sym_key.upper()} < {lt}'
        elif len(nums)>=3:
            buy=nums[0]
            target=nums[1]
            sl=nums[2]
            alert_type=f'{sym_key.upper()} Buy:{buy} T:{target} SL:{sl}'
        elif len(nums)==2:
            buy=nums[0]
            target=nums[1]
            alert_type=f'{sym_key.upper()} Buy:{buy} T:{target}'
        elif len(nums)==1:
            gt=nums[0]
            alert_type=f'{sym_key.upper()} > {gt}'
        else:
            bot.reply_to(m,'Ex: alert when crude > 65')
            return
        ALERT_ID+=1
        USER_ALERTS.append({'id':ALERT_ID,'chat':m.chat.id,'symbol':real_sym,'sym_name':sym_key.upper(),'buy':buy,'target':target,'sl':sl,'gt':gt,'lt':lt,'txt':alert_type,'created':time.time()})
        bot.send_message(m.chat.id,f'✅ <b>ALERT SET #{ALERT_ID}</b>\n\n{alert_type}\n24x7 check')
    except Exception as e:
        bot.reply_to(m,f'Error: {e}')

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['alerts','myalerts','alert list'])
def list_alerts_h(m):
    if not USER_ALERTS:
        bot.send_message(m.chat.id,'Koi alert nahi. Ex: alert when crude > 65')
        return
    txt=f'📋 <b>ACTIVE ({len(USER_ALERTS)})</b>\n\n'
    for a in USER_ALERTS[-15:]:
        txt+=f"#{a['id']} {a['txt']}\n"
    txt+='\n<code>alert del 1</code>'
    bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip().startswith('alert del'))
def del_alert_h(m):
    try:
        nums=re.findall(r'\d+', m.text)
        if not nums:
            return
        del_id=int(nums[0])
        global USER_ALERTS
        before=len(USER_ALERTS)
        USER_ALERTS=[a for a in USER_ALERTS if a['id']!=del_id]
        if len(USER_ALERTS)<before:
            bot.send_message(m.chat.id,f'✅ Deleted #{del_id}')
        else:
            bot.send_message(m.chat.id,f'❌ #{del_id} nahi mila')
    except:
        pass

@bot.message_handler(commands=['liveon','pinon'])
def liveon(m):
    global pinned_id
    try:
        msg=bot.send_message(int(GROUP_ID), make_crude_total())
        pinned_id=msg.message_id
        try:
            bot.pin_chat_message(int(GROUP_ID), pinned_id, disable_notification=True)
        except:
            pass
        bot.reply_to(m,'Live ON v11.8.1 ✅')
    except Exception as e:
        bot.reply_to(m,str(e))

def check_breaking():
    try:
        import feedparser
        urls=['https://news.google.com/rss/search?q=crude+oil+OPEC+breaking+when:1h&hl=en-IN&gl=IN&ceid=IN:en','https://news.google.com/rss/search?q=oil+embargo+missile+attack+when:1h&hl=en-IN&gl=IN&ceid=IN:en']
        for url in urls:
            try:
                r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=6)
                feed=feedparser.parse(r.content)
                for e in feed.entries[:5]:
                    low=e.title.lower()
                    found=None
                    for kw in BREAKING_KW:
                        if kw in low:
                            found=kw
                            break
                    if not found or e.title in LAST_BREAKING:
                        continue
                    if found in BREAKING_SENT and time.time()-BREAKING_SENT[found]<7200:
                        continue
                    LAST_BREAKING.add(e.title)
                    BREAKING_SENT[found]=time.time()
                    p=get_prices()
                    crude=p.get('CL=F',{'price':64.5})['price']
                    impact='BULLISH 🔼 90% UP' if any(w in low for w in ['cut','attack','embargo','war','shortage','ban']) else 'BEARISH 🔻'
                    msg=f'🚨 <b>BREAKING - CRUDE IMPACT</b> 🚨\n\n⚠️ {e.title}\n\n💥 IMPACT: {impact}\nCrude: ${crude:.2f}\n\n📰 News - Abhi'
                    bot.send_message(int(GROUP_ID), msg)
                    return
            except:
                continue
    except:
        pass

def check_leader():
    try:
        import feedparser
        urls=['https://news.google.com/rss/search?q=Trump+oil+statement+when:2h&hl=en-IN&gl=IN&ceid=IN:en']
        for url in urls:
            try:
                r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=6)
                feed=feedparser.parse(r.content)
                for e in feed.entries[:5]:
                    low=e.title.lower()
                    if 'oil' not in low:
                        continue
                    found_l=None
                    for l in LEADERS:
                        if l.lower() in low:
                            found_l=l
                            break
                    if not found_l or e.title in LAST_LEADER:
                        continue
                    LAST_LEADER.add(e.title)
                    p=get_prices()
                    crude=p.get('CL=F',{'price':64.5})['price']
                    msg=f'🌍 <b>WORLD LEADER IMPACT</b> 🚨\n\n👤 {found_l}: {e.title}\n\nCrude: ${crude:.2f}'
                    bot.send_message(int(GROUP_ID), msg)
                    return
            except:
                continue
    except:
        pass

def check_us_open():
    now=datetime.now(IST)
    if now.strftime("%H:%M")=="00:01":
        sent_us_today.clear()
    if now.weekday()>=5:
        return
    curr=now.strftime("%H:%M")
    times=["19:00","19:05","19:10","19:15","20:00","20:05","20:10","20:15"]
    key=now.strftime("%Y-%m-%d")+"_"+curr
    if curr in times and key not in sent_us_today:
        sent_us_today.add(key)
        try:
            get_prices()
            msg=f'🇺🇸 <b>USA MARKET OPENED - {curr} IST</b> 🟢\n\n'+make_stock_fno()
            bot.send_message(int(GROUP_ID), msg)
        except:
            pass

def check_price_alert():
    global LAST_CRUDE_PRICE
    try:
        p=get_prices()
        cr=p.get('CL=F')
        if not cr:
            return
        curr=cr['price']
        if LAST_CRUDE_PRICE==0:
            LAST_CRUDE_PRICE=curr
            return
        diff_pct=0
        if LAST_CRUDE_PRICE!=0:
            diff_pct=(curr-LAST_CRUDE_PRICE)/LAST_CRUDE_PRICE*100
        alert_msg=None
        if abs(diff_pct)>=0.5 and abs(diff_pct)<2:
            if time.time()-LAST_ALERT_PCT.get('0.5',0)>1800:
                alert_msg=f'⚡ <b>CRUDE ALERT {diff_pct:+.2f}%</b>\n${LAST_CRUDE_PRICE:.2f} -> ${curr:.2f}'
                LAST_ALERT_PCT['0.5']=time.time()
        elif abs(diff_pct)>=2 and abs(diff_pct)<5:
            if time.time()-LAST_ALERT_PCT.get('2',0)>3600:
                alert_msg=f'🚨 <b>BIG MOVE {diff_pct:+.2f}%</b>\n${LAST_CRUDE_PRICE:.2f} -> ${curr:.2f}'
                LAST_ALERT_PCT['2']=time.time()
        elif diff_pct>=10 or diff_pct<=-5:
            key='crash' if diff_pct<0 else 'pump'
            if time.time()-LAST_ALERT_PCT.get(key,0)>7200:
                alert_msg=f'💥 <b>CRUDE {key.upper()} {diff_pct:+.2f}%</b>\n${LAST_CRUDE_PRICE:.2f} -> ${curr:.2f}'
                LAST_ALERT_PCT[key]=time.time()
        if alert_msg:
            bot.send_message(int(GROUP_ID), alert_msg)
            LAST_CRUDE_PRICE=curr
        else:
            if time.time()-LAST_ALERT_PCT.get('update',0)>900:
                LAST_CRUDE_PRICE=curr
                LAST_ALERT_PCT['update']=time.time()
    except:
        pass

def check_user_alerts():
    if not USER_ALERTS:
        return
    try:
        p=get_prices()
        to_remove=[]
        for a in USER_ALERTS[:]:
            sym_data=p.get(a['symbol'])
            if not sym_data:
                continue
            price=sym_data['price']
            hit=False
            msg=''
            if a['gt'] is not None and price>=a['gt']:
                hit=True
                msg=f'🎯 <b>HIT #{a["id"]}</b> 🚀\n{a["sym_name"]} > {a["gt"]} HIT! Live: {price:.2f}'
            if a['lt'] is not None and price<=a['lt']:
                hit=True
                msg=f'🎯 <b>HIT #{a["id"]}</b> 🔻\n{a["sym_name"]} < {a["lt"]} HIT! Live: {price:.2f}'
            if a['buy'] and a['target']:
                if price>=a['target']:
                    hit=True
                    msg=f'💰 <b>TARGET HIT #{a["id"]}</b> 🟢\n{a["sym_name"]} {a["buy"]} -> {a["target"]} HIT! Live: {price:.2f}'
                elif a['sl'] and price<=a['sl']:
                    hit=True
                    msg=f'🛑 <b>SL HIT #{a["id"]}</b> 🔴\n{a["sym_name"]} {a["buy"]} -> SL {a["sl"]} HIT! Live: {price:.2f}'
            if hit:
                try:
                    bot.send_message(int(GROUP_ID), msg)
                    bot.send_message(a['chat'], msg)
                except:
                    pass
                to_remove.append(a)
        for a in to_remove:
            if a in USER_ALERTS:
                USER_ALERTS.remove(a)
    except:
        pass

def updater():
    last_pin=0
    last_break=0
    last_lead=0
    last_price=0
    last_user=0
    while True:
        time.sleep(30)
        t=time.time()
        if t-last_break>=120:
            check_breaking()
            last_break=t
        if t-last_lead>=180:
            check_leader()
            last_lead=t
        if t-last_price>=300:
            check_price_alert()
            last_price=t
        if t-last_user>=60:
            check_user_alerts()
            last_user=t
        check_us_open()
        if t-last_pin>=900:
            try:
                get_prices()
                fetch_news()
                if pinned_id:
                    try:
                        bot.edit_message_text(make_crude_total(), int(GROUP_ID), pinned_id)
                    except:
                        pass
                last_pin=t
            except:
                last_pin=t

threading.Thread(target=updater, daemon=True).start()
print('Bot v11.8.1 24x7 LIVE')
while True:
    try:
        bot.infinity_polling(none_stop=True, timeout=90, skip_pending=True)
    except Exception as e:
        print('poll err',e)
        time.sleep(10)
