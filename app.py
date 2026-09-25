
import os
import threading
import time
from flask import Flask
import telebot

# Paşam token Render'dan geliyor
BOT_TOKEN = os.getenv("BOT_TOKEN")
print(f"BOT_TOKEN var mi paşam? { 'EVET' if BOT_TOKEN else 'HAYIR - EKSIK!' }")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Senin Betano verilerin paşam - burası sende vardı
son_veriler = [13.69, 7.84, 7.85, 14.32, 18.09, 19.93, 11.68, 8.7, 8.71, 10.33, 19.43, 15.59, 10.74, 5.87, 13.87, 3.06, 9.88, 17.0, 10.63, 6.72]

@app.route('/')
def home():
    return f"<h1>Sharo Bot Calisiyor!</h1><br>Son: {son_veriler}<br><br>PAŞAM BOT AKTIF!"

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, "PAŞAM BOT AKTİF! 🔥\n\nBetano izleniyor!\n\nKomutlar:\n/start - Botu baslat\n/durum - Son verileri gor")

@bot.message_handler(commands=['durum'])
def durum_cmd(message):
    bot.reply_to(message, f"Son veriler paşam: {son_veriler}")

@bot.message_handler(func=lambda m: True)
def all_msg(message):
    bot.reply_to(message, "Paşam /start yaz! Bot aktif!")

def run_telegram():
    print("PAŞAM TELEGRAM BOT BAŞLIYOR...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Paşam bot hatasi: {e}")
            time.sleep(5)

# WEBSITE + TELEGRAM AYNI ANDA CALISSIN PAŞAM
if __name__ == '__main__':
    # Telegram'i arka planda baslat paşam
    threading.Thread(target=run_telegram, daemon=True).start()
    # Website'yi baslat
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
