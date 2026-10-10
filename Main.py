import os, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"OK LIVE")
 def do_HEAD(self):
  self.send_response(200)
  self.end_headers()
 def log_message(self, *a): pass

def run_health():
 port = int(os.environ.get("PORT", 10000))
 HTTPServer(("0.0.0.0", port), H).serve_forever()

threading.Thread(target=run_health, daemon=True).start()

import telebot, time
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1004448478970"))
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
IST = pytz.timezone("Asia/Kolkata")
pinned_id = None

def get_plan():
  text = ""
  text += "<b>NIFTY 50 - TRADE PLAN</b>\n"
  text += "<b>MONDAY 12 OCT 2026</b> | Educational\n"
  text += "--------------------------\n"
  text += "FAST READ\n"
  text += "LONG: 22,580 upar = LONG 22,600\n"
  text += "SHORT: 22,180 tode + 22,220 fail = SHORT\n"
  text += "Make-or-Break = 22,180\n"
  text += "--------------------------\n"
  text += "LEVELS\n"
  text += "Res: 22,580 -> 22,600 -> 22,775 -> 22,950\n"
  text += "Sup: 22,400 -> 22,350 -> 22,220 -> 22,180 -> 22,000\n"
  text += "--------------------------\n"
  text += "PLAN A [9:30-11:00] LONG 22,600 SL 22,480 TGT 22,775-22,950\n"
  text += "PLAN B [9:30-12:30] LONG 22,400 SL 22,140 TGT 22,580-22,775\n"
  text += "PLAN C [Anytime] SHORT 22,180 SL 22,340 TGT 22,000\n"
  text += "After 2:45 PM No New Trades\n"
  return text

def get_hi():
  now = datetime.now(IST).strftime("%I:%M %p, %d %b")
  text = ""
  text += "<b>PATIALA CRUDE LIVE - " + now + "</b>\n\n"
  text += "CRUDE OIL: Live Data\n"
  text += "Trend: STABLE\n\n"
  text += "NIFTY: Monitoring\n\n"
  text += "Type plan for Trade Plan\n"
  return text

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["hi","hii","hello","status"])
def hi_handler(m):
 bot.send_message(m.chat.id, get_hi())

@bot.message_handler(func=lambda m: m.text and "plan" in m.text.lower())
def plan_handler(m):
 bot.send_message(m.chat.id, get_plan())

@bot.message_handler(commands=["liveon","pinon"])
def liveon(m):
 global pinned_id
 msg = bot.send_message(GROUP_ID, get_hi())
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
     bot.edit_message_text(get_hi(), GROUP_ID, pinned_id)
    except:
     pass
  except:
   time.sleep(60)

threading.Thread(target=updater, daemon=True).start()

while True:
    try:
        print("Bot polling started 15 min mode")
        bot.infinity_polling(none_stop=True, timeout=90, skip_pending=True)
    except Exception as e:
        print(f"Polling error {e}")
        time.sleep(10)
