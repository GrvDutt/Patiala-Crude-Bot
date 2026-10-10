# CRUDE BOT v12.0 NOVA - FIXED FINAL
import os, threading, time, requests, telebot, re
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'OK NOVA')
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
    def log_message(self,*a): pass

def run_health():
    HTTPServer(('0.0.0.0', int(os.environ.get('PORT','10000'))), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

BOT_TOKEN=os.getenv('BOT_TOKEN')
GROUP_ID=os.getenv('GROUP_ID','-1004448478970')
bot=telebot.TeleBot(BOT_TOKEN, parse_mode='HTML', threaded=False, disable_web_page_preview=True)

CACHE={'prices':{}, 'news':'Loading...', 'time':0}
USER_ALERTS=[]; ALERT_ID=0
LAST_BIG=set(); LAST_BIG_BUYER=0
SYMBOLS=['CL=F','^NSEI','^BSESN','GC=F','INR=X','USO']
SYMBOL_MAP={'crude':'CL=F','nifty':'^NSEI','sensex':'^BSESN','gold':'GC=F','uso':'USO'}
pinned_id=None

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
                v1=float(h['Volume'].iloc[-1])
                v2=float(h['Volume'].tail(5).mean())
                prices[sym]={'price':c,'change':ch,'vol':v1,'vavg':v2}
            except: continue
    except: pass
    if prices:
        CACHE['prices']=prices; CACHE['time']=time.time()
    return CACHE['prices']

def fetch_news():
    try:
        import feedparser
        url='https://news.google.com/rss/search?q=crude+oil+OPEC+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        r=requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=6)
        feed=feedparser.parse(r.content)
        txt=''
        for i,e in enumerate(feed.entries[:5],1):
            t=e.title[:75]
            link=e.link
            low=t.lower()
            if any(w in low for w in ['up','rise','cut','war','buy']):
                arrow='UP'
            elif any(w in low for w in ['down','fall','sell','surplus']):
                arrow='DOWN'
            else:
                arrow='SIDE'
            txt+=f'{i}. <a href="{link}">{t}</a> {arrow}\n\n'
        CACHE['news']=txt if txt else 'Market stable\n'
    except:
        CACHE['news']='Market stable\n'

def make_crude():
    p=get_prices(); cr=p.get('CL=F')
    if not cr: return 'Loading...'
    usd=p.get('INR=X',{'price':84})['price']
    rs=int(cr['price']*usd)
    icon='UP' if cr['change']>=0 else 'DOWN'
    return f'CRUDE TOTAL {icon}\n${cr["price"]:.2f} | Rs {rs} ({cr["change"]:+.2f}%)\n\n{CACHE["news"]}'

def make_stock():
    p=get_prices(); cr=p.get('CL=F',{'price':64,'change':0})
    b='UP' if cr['change']>0 else 'DOWN'
    return f'F&O SCALP {b}\nCrude ${cr["price"]:.2f} ({cr["change"]:+.2f}%)'

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ['hi','hello','crude'])
def hi_h(m): bot.send_message(m.chat.id, make_crude())

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip()=='news')
def news_h(m): bot.send_message(m.chat.id, f'NEWS\n\n{CACHE["news"]}')

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip()=='stock')
def stock_h(m): bot.send_message(m.chat.id, make_stock())

@bot.message_handler(func=lambda m: '?' in m.text)
def help_h(m):
    bot.send_message(m.chat.id, 'hi, news, stock, alert when crude > 65, alerts, /liveon')

@bot.message_handler(commands=['liveon'])
def liveon(m):
    global pinned_id
    msg=bot.send_message(int(GROUP_ID), make_crude())
    pinned_id=msg.message_id
    bot.reply_to(m,'LIVE ON')

threading.Thread(target=lambda:(get_prices(),fetch_news()), daemon=True).start()
print('Bot v12.0 NOVA LIVE')
bot.infinity_polling(none_stop=True, timeout=90)
