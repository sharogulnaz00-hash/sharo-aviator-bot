import os
import threading
from flask import Flask, request, jsonify
import telebot
from collections import deque

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = None

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None

history = deque(maxlen=100)
kasa = 1000.0
martingale_step = 0
signal_active = False
martingale_bets = [10, 30, 90]

def send_telegram(msg):
    global CHAT_ID
    if bot and CHAT_ID:
        try:
            bot.send_message(CHAT_ID, msg, parse_mode='HTML')
        except Exception as e:
            print(f"Telegram hatasi: {e}")

def process_result(value):
    global kasa, martingale_step, signal_active
    try:
        value = float(value)
    except:
        return
    history.append(value)
    print(f"Yeni oran: {value} - Gecmis: {list(history)[-10:]}")

    if len(history) >= 5:
        last5 = list(history)[-5:]
        if all(v < 1.5 for v in last5):
            if not signal_active:
                signal_active = True
                martingale_step = 0
                send_telegram(f"🚨 <b>SINYAL PASAM!</b>\n5 dusuk geldi: {last5}\n<b>BAHIS: {martingale_bets[0]}€ @ 1.5x</b>")
                return

    if signal_active:
        if value >= 1.5:
            kazanc = martingale_bets[martingale_step] * 0.5
            kasa += kazanc
            send_telegram(f"✅ <b>KAZANDI PASAM!</b>\nBahis: {martingale_bets[martingale_step]}€ -> {martingale_bets[martingale_step]*1.5}€\nKASA: {kasa:.1f}€")
            signal_active = False
            martingale_step = 0
        else:
            kasa -= martingale_bets[martingale_step]
            martingale_step += 1
            if martingale_step < 3:
                send_telegram(f"⚠️ <b>{martingale_step}. ADIM YATTI PASAM!</b>\n{value}x geldi\nYeni bahis: {martingale_bets[martingale_step]}€\nKASA: {kasa:.1f}€")
            else:
                send_telegram(f"❌ <b>KAYBETTI PASAM -130€</b>\nKASA: {kasa:.1f}€")
                signal_active = False
                martingale_step = 0

@app.route("/")
def home():
    return f"Kasa: {kasa} | Gecmis: {list(history)[-10:]} | Durum: AKTIF"

@app.route("/api/data", methods=["POST"])
def receive_data():
    data = request.json
    if not data:
        return jsonify({"error": "no data"}), 400
    val = data.get("value", 0)
    process_result(val)
    return jsonify({"ok": True, "kasa": kasa})

@bot.message_handler(commands=['start'])
def start_cmd(m):
    global CHAT_ID
    CHAT_ID = m.chat.id
    bot.reply_to(m, f"PASAM BOT AKTIF! 🔥\nKASA: {kasa}€\n/test 1.23 ile test et!")

@bot.message_handler(commands=['test'])
def test_cmd(m):
    try:
        parts = m.text.split()
        v = float(parts[1])
        process_result(v)
        bot.reply_to(m, f"Test eklendi: {v}x | Kasa: {kasa}")
    except:
        bot.reply_to(m, "Kullanim: /test 1.23")

@bot.message_handler(func=lambda m: True)
def all_msg(m):
    global CHAT_ID
    CHAT_ID = m.chat.id

def telegram_polling():
    if bot:
        print("Telegram polling basladi")
        bot.infinity_polling()

threading.Thread(target=telegram_polling, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
