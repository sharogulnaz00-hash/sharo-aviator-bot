import os
import threading
import time
from flask import Flask
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("HATA PASAM: BOT_TOKEN YOK!")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ===== AYARLAR =====
KASA_BASLANGIC = 1000.0
kasa = KASA_BASLANGIC
BAHISLER = [10, 30, 90] # Dogru martingale 1.50 icin, her kazanc +5 euro
HEDEF = 1.50

son_veriler = [13.69, 7.84, 1.2, 1.1, 1.3, 1.4, 1.2]
aktif = False
adim = 0
CHAT_IDS = set()

def bildirim(mesaj):
    for cid in list(CHAT_IDS):
        try:
            bot.send_message(cid, mesaj, parse_mode='HTML')
        except:
            pass

def isle(yeni_oran):
    global kasa, aktif, adim, son_veriler
    son_veriler.append(yeni_oran)
    if len(son_veriler) > 200:
        son_veriler = son_veriler[-200:]

    print(f"Oran geldi: {yeni_oran} Kasa: {kasa}")

    # Martingale kontrol
    if aktif:
        bahis = BAHISLER[adim]
        if yeni_oran >= HEDEF:
            kasa += bahis * 1.5
            msg = f"✅ <b>KAZANDI PASAM!</b>\n📈 Oran: {yeni_oran}x\n💵 Bahis: {bahis}€ -> {bahis*1.5}€\n💰 KASA: {round(kasa,2)}€\n📊 Adim: {adim+1}/3 - KAR +5€"
            bildirim(msg)
            aktif = False
            adim = 0
        else:
            if adim == 2:
                msg = f"❌ <b>KAYBETTI PASAM!</b>\n📉 Oran: {yeni_oran}x\n💸 Zarar: -{sum(BAHISLER)}€\n💰 KASA: {round(kasa,2)}€"
                bildirim(msg)
                aktif = False
                adim = 0
            else:
                adim += 1
                yeni_bahis = BAHISLER[adim]
                kasa -= yeni_bahis
                msg = f"⚠️ <b>{adim}. adim yatti</b> {yeni_oran}x\n➡️ {adim+1}. adim {yeni_bahis}€ basildi\n💰 Kasa: {round(kasa,2)}€"
                bildirim(msg)
        return

    # Tetik kontrol - 5 kez < 2.0
    if len(son_veriler) >= 5:
        son5 = son_veriler[-5:]
        if all(x < 2.0 for x in son5):
            aktif = True
            adim = 0
            bahis = BAHISLER[0]
            kasa -= bahis
            msg = f"🚨 <b>SINYAL PASAM!</b> 🚨\n5 kez <2x geldi!\nSon 5: {son5}\n\n💰 {bahis}€ GIRIS\n🎯 Hedef: 1.50x\n💰 Kasa: {round(kasa,2)}€"
            bildirim(msg)

@app.route('/')
def home():
    s5 = son_veriler[-5:] if len(son_veriler)>=5 else son_veriler
    return f"<h1>Sharo Bot 2.0 Calisiyor!</h1><p>Kasa: {round(kasa,2)}€ | Aktif: {aktif} Adim:{adim+1}</p><p>Son 5: {s5}</p><p>Son 20: {son_veriler[-20:]}</p>"

@bot.message_handler(commands=['start'])
def start(m):
    CHAT_IDS.add(m.chat.id)
    bot.reply_to(m, f"PASAM BOT AKTIF! 🔥\nKasa: {round(kasa,2)}€\n\n5x <2x -> 10/30/90 -> 1.50x\n\nKomutlar:\n/durum\n/kasa\n/test 1.2")

@bot.message_handler(commands=['durum'])
def durum(m):
    bot.reply_to(m, f"Son 5: {son_veriler[-5:]}\nKasa: {round(kasa,2)}€\nAktif: {aktif} Adim: {adim+1}")

@bot.message_handler(commands=['kasa'])
def kasa_cmd(m):
    bot.reply_to(m, f"KASA: {round(kasa,2)}€")

@bot.message_handler(commands=['test'])
def test_cmd(m):
    try:
        oran = float(m.text.split()[1].replace(',', '.'))
        isle(oran)
        bot.reply_to(m, f"Eklendi: {oran}x | Kasa: {round(kasa,2)}€")
    except:
        bot.reply_to(m, "Ornek: /test 1.2")

def run_bot():
    print("PASAM BOT BASLIYOR...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot hata: {e}")
            time.sleep(5)

def fake_data():
    import random
    while True:
        time.sleep(10)
        r = random.uniform(1.05, 1.99) if random.random() < 0.75 else random.uniform(2.0, 15.0)
        r = round(r, 2)
        isle(r)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=fake_data, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
