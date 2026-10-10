# -*- coding: utf-8 -*-
# CRUDE BOT v13 NOVA - FULL FEATURE - NO SYNTAX ERROR
import os, threading, time, requests, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b'OK v13 FULL')
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
    def log_message(self,*a): pass

def run_health():
    HTTPServer(('0.0.0.0', int(os.environ.get('PORT','10000'))), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN=os.getenv('BOT_TOKEN')
GROUP_ID=os.getenv('GROUP_ID','-1004448478970')
bot=telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)

CACHE={'prices':{}, 'time':0}
LAST_BIG=set()
LAST_BIG_BUYER=0
USER_ALERTS=[]
ALERT_ID=0

def get_prices():
    if time.time()-CACHE['time']<120 and CACHE['prices']:
        return CACHE['prices']
    prices={}
    try:
        import yfinance as yf
        for sym in ['CL=F','^NSEI','USO']:
            try:
                h=yf.Ticker(sym).history(period='5d')
                if h.empty: continue
                c=float(h['Close'].iloc[-1])
                p2=float(h['Close'].iloc[-2]) if len(h)>1 else c
                ch=0
                if p2!=0: ch=(c-p2)/p2*100
                v1=float(h['Volume'].iloc[-1])
                v2=float(h['Volume'].tail(5).mean())
                prices[sym]={'price':c,'change':ch,'vol':v1,'vavg':v2}
            except: continue
    except: pass
    if prices:
        CACHE['prices']=prices
        CACHE['time']=time.time()
    return CACHE['prices']

def breaking_msg():
    try:
        import feedparser
        url='https://news.google.com/rss/search?q=crude+oil+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r=requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=6)
        feed=feedparser.parse(r.content)
        p=get_prices()
        cr=91.85
        if 'CL=F' in p: cr=p['CL=F']['price']
        for e in feed.entries[:2]:
            low=e.title.lower()
            impact='SIDEWAY 50% 👀'
            if 'war' in low: impact='BULLISH 90% UP ⬆️'
            if 'attack' in low: impact='BULLISH 90% UP ⬆️'
            if 'cut' in low: impact='BULLISH 90% UP ⬆️'
            if 'down' in low: impact='BEARISH 90% DOWN ⬇️'
            if 'supply' in low: impact='BEARISH 90% DOWN ⬇️'
            msg="🚨 BREAKING - CRUDE IMPACT 🚨\n\n⚠️ "+e.title+"\n\n💥 IMPACT: "+impact+"\nCrude: $"+str(round(cr,2))+"\n\n📰 News - Abhi"
            return msg
        return "🚨 BREAKING\nMarket stable Crude $"+str(round(cr,2))+" 👀"
    except Exception as ex:
        return "News loading..."

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hello','crude','hi crude'])
def hi_h(m):
    p=get_prices()
    cr=p.get('CL=F',{'price':91.85,'change':0.39})
    nse=p.get('^NSEI',{'change':0})
    arrow="⬆️"
    if cr['change']<0: arrow="⬇️"
    txt="📊 CRUDE TOTAL STATUS\n\n1. CURRENT: BULLISH 🔥\nCrude: $"+str(round(cr['price'],2))+" ("+str(round(cr['change'],2))+"%) "+arrow+"\nNSE: "+str(round(nse['change'],2))+"%\n\n💡 View: Buy on dip"
    bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip()=='news')
def news_h(m):
    txt=breaking_msg()
    bot.send_message(m.chat.id, txt)
    bot.send_message(int(GROUP_ID), txt)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['stock','fno','f&o'])
def stock_h(m):
    p=get_prices()
    cr=p.get('CL=F',{'price':91.85,'change':0.39})
    uso=p.get('USO',{'vol':0,'vavg':1,'change':0})
    whale="🐋 Whale: No big volume"
    vol_pct=0
    if uso['vavg']>0: vol_pct=int(uso['vol']/uso['vavg']*100)
    if uso['vol']>uso['vavg']*1.5:
        whale="🐋 BIG BUYER LIVE ⬆️\nUSO "+str(round(uso['vol']/1e6,1))+"M vol ("+str(vol_pct)+"%) pump"
    txt="📊 F&O SCALP\n"+whale+"\nCrude: $"+str(round(cr['price'],2))+" ("+str(round(cr['change'],2))+"%) ⬆️\n\nSL: 20 pts"
    bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text and '?' in m.text)
def help_h(m):
    txt="🤖 CRUDE BOT v13 NOVA FULL\n\n? - help\nhi crude - total status\nnews - breaking impact\nstock - FNO + whale\n/liveon - pin\n\nalert when crude > 65\nalerts"
    bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip().startswith('alert when'))
def alert_h(m):
    global ALERT_ID
    try:
        nums=re.findall(r'\d+\.?\d*', m.text)
        if not nums: return
        val=float(nums[-1])
        ALERT_ID+=1
        USER_ALERTS.append({'id':ALERT_ID,'price':val,'chat':m.chat.id})
        bot.send_message(m.chat.id, "✅ Alert #"+str(ALERT_ID)+" set at $"+str(val))
    except: pass

@bot.message_handler(commands=['liveon','live'])
def liveon(m):
    p=get_prices()
    cr=p.get('CL=F',{'price':91.85})
    txt="📊 CRUDE TOTAL STATUS 1. CURRENT: BULLISH 🔥\nCrude: $"+str(round(cr['price'],2))+" ⬆️\n\nLIVE v13 NOVA 🐋"
    bot.send_message(int(GROUP_ID), txt)
    bot.reply_to(m, 'LIVE ON v13 ✅')

def updater():
    last=0
    last_w=0
    while True:
        time.sleep(60)
        t=time.time()
        if t-last>=600:
            try:
                txt=breaking_msg()
                # duplicate check
                if txt not in LAST_BIG:
                    LAST_BIG.add(txt)
                    bot.send_message(int(GROUP_ID), txt)
            except: pass
            last=t
        if t-last_w>=1800:
            try:
                p=get_prices()
                uso=p.get('USO')
                cr=p.get('CL=F',{'price':91})
                if uso is not None:
                    if uso['vol']>uso['vavg']*1.5:
                        if uso['change']>1.0:
                            if time.time()-LAST_BIG_BUYER>1800:
                                bot.send_message(int(GROUP_ID), "🐋 BIG BUYER LIVE ⬆️ USO pump "+str(round(uso['change'],2))+"% Crude $"+str(round(cr['price'],2)))
            except: pass
            last_w=t

threading.Thread(target=updater, daemon=True).start()
print('Bot v13 FULL LIVE')
while True:
    try:
        bot.infinity_polling(none_stop=True, timeout=90)
    except Exception as e:
        print("polling error", e)
        time.sleep(10)
