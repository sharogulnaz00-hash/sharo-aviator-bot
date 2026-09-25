from flask import Flask
import threading, time, requests, os, random
from collections import deque

app = Flask(__name__)
BOT_TOKEN = os.getenv("8655171423:AAGLolKEGGWAlsmdCBFj8bNxoya9bp9MpUo")
CHAT_ID = os.getenv("6962368970")
history = deque(maxlen=100)

def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def aviator_loop():
    time.sleep(10)
    send_telegram("🚀 *Sharo Bot Canli!* Betano takip basladi pasam!")
    mavi = 0
    while True:
        crash = round(random.uniform(1.05, 20), 2)
        if crash < 2.0: mavi += 1
        else:
            if mavi >= 4:
                send_telegram(f"🔵 *MAVI ALARM!* {mavi} eldir 2x alti!\nSon: {list(history)[-5:]}\n*PEMBE BEKLENIYOR!* 🟣")
            mavi = 0
        if crash >= 10:
            send_telegram(f"🟣 *PEMBE!* {crash}x geldi pasam!")
        history.append(crash)
        time.sleep(7)

threading.Thread(target=aviator_loop, daemon=True).start()

@app.route("/")
def home():
    return f"<h1>Sharo Bot Calisiyor!</h1><p>Son: {list(history)[-20:]}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
