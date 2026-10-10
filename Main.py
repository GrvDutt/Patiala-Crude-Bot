import os, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK v7.4 FINAL 15 MIN RED GREEN FIXED")
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get("PORT", 10000))
 HTTPServer(("0.0.0.0", port), H).serve_forever()
threading.Thread(target=run_health, daemon=True).start()

import pytz, requests, yfinance as yf, telebot, feedparser
from datetime import datetime
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004448478970"))
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
IST = pytz.timezone("Asia/Kolkata")
pinned_id = None

def get_inr():
 try:
  d = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()
  return d["rates"]["INR"]
 except:
  return 88.0

def get_data(sym):
 try:
  h = yf.Ticker(sym).history(period="2d")
  if h.empty:
   return None
  c = float(h["Close"].iloc[-1])
  p = float(h["Close"].iloc[-2]) if len(h)>1 else c
  ch = ((c-p)/p*100) if p else 0
  return {"price":c,"change":ch}
 except:
  return None

def color_fmt(ch, label):
 if ch > 0.10:
  return "🟢 " + label + " (+" + str(round(ch,2)) + "%)"
 if ch < -0.10:
  return "🔴 " + label + " (" + str(round(ch,2)) + "%)"
 return "🔵 " + label + " (" + str(round(ch,2)) + "% Stable)"

def get_news():
  try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=crude+oil+OPEC&hl=en-IN&gl=IN&ceid=IN:en")
    if feed.entries:
      txt = ""
      for i in range(3):
        h = feed.entries[i].title[:65].replace("<","").replace(">","")
        txt += str(i+1) + ". " + h + "\n"
      return txt
  except:
   pass
  return "1. OPEC supply in focus\n2. US inventory awaited\n3. Crude outlook stable\n"

def get_nifty_plan_text():
  lines = []
  lines.append("<b>📌 NIFTY 50 - TRADE PLAN</b>")
  lines.append("<b>MONDAY 12 OCT 2026</b> | Educational")
  lines.append("--------------------------")
  lines.append("FAST READ")
  lines.append("LONG: 22,580 upar = LONG 22,600")
  lines.append("SHORT: 22,180 tode + 22,220 fail = SHORT")
  lines.append("Make-or-Break = 22,180")
  lines.append("--------------------------")
  lines.append("LEVELS")
  lines.append("Res: 22,580 -> 22,600 -> 22,775 -> 22,950")
  lines.append("Sup: 22,400 -> 22,350 -> 22,220 -> 22,180 -> 22,000")
  lines.append("--------------------------")
  lines.append("PLAN A [9:30-11:00] LONG 22,600 SL 22,480 TGT 22,775-22,950")
  lines.append("PLAN B [9:30-12:30] LONG 22,400 SL 22,140 TGT 22,580-22,775")
  lines.append("PLAN C [Anytime] SHORT 22,180 SL 22,340 TGT 22,000")
  lines.append("After 2:45 PM -> No New Trades")
  return "\n".join(lines)

def make_hi_text():
 inr = get_inr()
 crude = get_data("CL=F")
 nifty = get_data("^NSEI")
 sensex = get_data("^BSESN")
 now = datetime.now(IST).strftime("%I:%M %p, %d %b")
 news = get_news()
 msg = "<b>📌 PATIALA CRUDE LIVE - " + now + "</b>\n\n"
 if crude:
  label = "$" + str(round(crude["price"],2)) + " (Rs " + str(int(crude["price"]*inr)) + ")"
  msg += "CRUDE OIL\n"
  msg += color_fmt(crude["change"], label) + "\n\n"
 if nifty:
  msg += "NIFTY: " + color_fmt(nifty["change"], str(round(nifty["price"],2))) + "\n"
 if sensex:
  msg += "SENSEX: " + color_fmt(sensex["change"], str(round(sensex["price"],2))) + "\n"
 msg += "\nNEWS\n" + news + "\n"
 msg += "Type plan for Trade Plan"
 return msg

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["hi","hii","hello","status"])
def hi_handler(m):
 bot.send_message(m.chat.id, make_hi_text())

@bot.message_handler(func=lambda m: m.text and "plan" in m.text.lower())
def plan_handler(m):
 bot.send_message(m.chat.id, get_nifty_plan_text())

@bot.message_handler(commands=["liveon","pinon"])
def liveon(m):
 global pinned_id
 msg = bot.send_message(GROUP_ID, make_hi_text())
 pinned_id = msg.message_id
 try:
  bot.pin_chat_message(GROUP_ID, pinned_id, disable_notification=True)
 except:
  pass

def updater():
 global pinned_id
 while True:
  try:
   time.sleep(900)
   print("15 min update tick")
   if pinned_id:
    try:
     bot.edit_message_text(make_hi_text(), GROUP_ID, pinned_id)
    except Exception as e:
     print("Edit error", e)
  except Exception as e:
   print("Updater error", e)
   time.sleep(60)

threading.Thread(target=updater, daemon=True).start()

while True:
    try:
        print("Bot polling started 15 min RED GREEN LIVE")
        bot.infinity_polling(none_stop=True, timeout=90, skip_pending=True)
    except Exception as e:
        print("Polling error", e)
        time.sleep(10)
