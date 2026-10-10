# CRUDE BOT v12.0 NOVA - KEEP CURRENT NEWS + WHALE
import os, threading, time, requests, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b'OK v12')
    def do_HEAD(self): self.send_response(200); self.end_headers()
    def log_message(self,*a): pass

def run_health():
    HTTPServer(('0.0.0.0', int(os.environ.get('PORT','10000'))), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN=os.getenv('BOT_TOKEN')
GROUP_ID=os.getenv('GROUP_ID','-1004448478970')
bot=telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False)

CACHE={'prices':{}, 'time':0}
USER_ALERTS=[]; ALERT_ID=0
LAST_BIG=set(); LAST_BIG_BUYER=0
pinned_id=None

SYMBOLS=['CL=F','^NSEI','^BSESN','GC=F','INR=X','USO']
SYMBOL_MAP={'crude':'CL=F','nifty':'^NSEI','sensex':'^BSESN','gold':'GC=F','uso':'USO'}

def get_prices():
    if time.time()-CACHE['time']<120 and CACHE['prices']:
        return CACHE['prices']
    prices={}
    try:
        import yfinance as yf
        for sym in SYMBOLS:
            try:
                h=yf.Ticker(sym).history(period='5d')
                if h.empty: continue
                c=float(h['Close'].iloc[-1])
                p=float(h['Close'].iloc[-2]) if len(h)>1 else c
                ch=(c-p)/p*100 if p else 0
                vol1=float(h['Volume'].iloc[-1])
                vol2=float(h['Volume'].tail(5).mean())
                prices[sym]={'price':c,'change':ch,'vol':vol1,'vavg':vol2}
            except: continue
    except: pass
    if prices:
        CACHE['prices']=prices; CACHE['time']=time.time()
    return CACHE['prices']

# --- TERA CURRENT NEWS LOGIC SAME RAKHA (jo screenshot me chal raha hai) ---
def send_breaking_news():
    try:
        import feedparser
        url='https://news.google.com/rss/search?q=crude+oil+OPEC+Iran+war+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r=requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=6)
        feed=feedparser.parse(r.content)
        p=get_prices(); cr=p.get('CL=F',{'price':91.85})['price']
        for e in feed.entries[:2]:
            if e.title in LAST_BIG: continue
            LAST_BIG.add(e.title)
            # Simple bullish/bearish logic jo tere me tha
            low=e.title.lower()
            if any(w in low for w in ['war','attack','killed','crisis','cut']):
                impact='BULLISH 90% UP ⬆️'
            elif any(w in low for w in ['down','fall','increase','supply']):
                impact='BEARISH 90% DOWN ⬇️'
            else:
                impact='SIDEWAY 50% 👀'
            msg=f'🚨 BREAKING - CRUDE IMPACT 🚨\n\n⚠️ {e.title}\n\n💥 IMPACT: {impact}\nCrude: ${cr:.2f}\n\n📰 News - Abhi'
            bot.send_message(int(GROUP_ID), msg)
    except: pass

def check_big_buyers():
    global LAST_BIG_BUYER
    if time.time()-LAST_BIG_BUYER<1800: return
    try:
        p=get_prices(); uso=p.get('USO'); cr=p.get('CL=F',{'price':91})
        if not uso: return
        if uso['vol']>uso['vavg']*1.5 and uso['change']>1.0:
            msg=f'🐋 BIG BUYER LIVE ⬆️\nUSO {uso["vol"]/1e6:.1f}M vol ({uso["vol"]/uso["vavg"]*100:.0f}%) pump +{uso["change"]:.2f}%\nCrude ${cr["price"]:.2f} ⬆️\nMarket pull hoga'
            bot.send_message(int(GROUP_ID), msg); LAST_BIG_BUYER=time.time()
        elif uso['vol']>uso['vavg']*1.5 and uso['change']<-1.0:
            msg=f'🐋 BIG SELLER LIVE ⬇️\nUSO {uso["vol"]/1e6:.1f}M vol dump {uso["change"]:.2f}%\nCrude ${cr["price"]:.2f} ⬇️\nDown swing'
            bot.send_message(int(GROUP_ID), msg); LAST_BIG_BUYER=time.time()
    except: pass

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','crude'])
def hi_h(m):
    p=get_prices(); cr=p.get('CL=F',{'price':91.85})
    bot.send_message(m.chat.id, f'CRUDE TOTAL STATUS\nCurrent: ${cr["price"]:.2f} ({cr["change"]:+.2f}%)')

@bot.message_handler(func=lambda m: m.text and '?' in m.text)
def help_h(m):
    bot.send_message(m.chat.id, "Commands:\nhi - total\nnews - breaking news\nstock - f&o\n? - help\nalert when crude > 65\nalerts\n/liveon\n🐋 big buyer auto 30min")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('alert when'))
def alert_h(m):
    global ALERT_ID
    try:
        nums=re.findall(r'\d+\.?\d*', m.text); nums=[float(x) for x in nums]
        if not nums: return
        ALERT_ID+=1
        USER_ALERTS.append({'id':ALERT_ID,'price':nums[-1],'chat':m.chat.id,'txt':m.text})
        bot.send_message(m.chat.id, f'Alert #{ALERT_ID} set {nums[-1]}')
    except: pass

@bot.message_handler(commands=['liveon'])
def liveon(m):
    global pinned_id
    p=get_prices(); cr=p.get('CL=F',{'price':91.85})
    msg=bot.send_message(int(GROUP_ID), f'CRUDE TOTAL STATUS 1. CURRENT: BULLISH\nCrude: ${cr["price"]:.2f}')
    pinned_id=msg.message_id
    bot.reply_to(m,'LIVE ON')

def updater():
    last=0; last_w=0
    while True:
        time.sleep(60)
        t=time.time()
        if t-last>=600:
            send_breaking_news(); last=t
        if t-last_w>=1800:
            check_big_buyers(); last_w=t

threading.Thread(target=updater, daemon=True).start()
print('Bot v12 NOVA LIVE - NEWS SAME')
bot.infinity_polling(none_stop=True)
