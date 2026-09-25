import os, time, threading, requests, re
from flask import Flask, request, jsonify
import telebot
from collections import deque

BOT_TOKEN = os.getenv("BOT_TOKEN")
BETANO_USER = os.getenv("BETANO_USER")
BETANO_PASS = os.getenv("BETANO_PASS")
CHAT_ID = None

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None

history = deque(maxlen=100)
kasa = 1000.0
bet_amount = 10
martingale_step = 0
signal_active = False
martingale_bets = [10, 30, 90]

last_crash = None

def send_telegram(msg):
    if bot and CHAT_ID:
        try:
            bot.send_message(CHAT_ID, msg, parse_mode='HTML')
        except Exception as e:
            print(f"Telegram hatası: {e}")

def process_result(value):
    global kasa, martingale_step, signal_active, last_crash
    if last_crash == value:
        return
    last_crash = value
    history.append(value)
    print(f"Yeni oran: {value}x | Geçmiş: {list(history)[-10:]}")

    # STRATEJİ: 5 pembe üst üste düşük (1.5 altı)
    if len(history) >= 5:
        last5 = list(history)[-5:]
        if all(v < 1.5 for v in last5):
            if not signal_active:
                signal_active = True
                martingale_step = 0
                send_telegram(f"🚨 <b>SİNYAL PAŞAM!</b>\n5 düşük geldi: {last5}\n<b>BAHİS: {martingale_bets[0]}€ @ 1.5x</b>")
                return

    if signal_active:
        if value >= 1.5:
            kazanc = martingale_bets[martingale_step] * 1.5 - martingale_bets[martingale_step]
            kasa += kazanc
            send_telegram(f"✅ <b>KAZANDI PAŞAM!</b>\nBahis: {martingale_bets[martingale_step]}€ -> {martingale_bets[martingale_step]*1.5}€\nKASA: {kasa:.1f}€")
            signal_active = False
            martingale_step = 0
        else:
            kasa -= martingale_bets[martingale_step]
            martingale_step += 1
            if martingale_step < 3:
                send_telegram(f"⚠️ <b>{martingale_step}. ADIM YATTI PAŞAM!</b>\n{value}x geldi\nYeni bahis: {martingale_bets[martingale_step]}€\nKASA: {kasa:.1f}€")
            else:
                send_telegram(f"❌ <b>KAYBETTİ PAŞAM -130€</b>\nKASA: {kasa:.1f}€")
                signal_active = False
                martingale_step = 0

def betano_scraper():
    print("Betano scraper başlıyor paşam...")
    time.sleep(10) # Flask başlasın
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            print("Betano.bg'ye gidiliyor...")
            page.goto("https://www.betano.bg/", timeout=60000)
            time.sleep(5)

            # Login dene
            try:
                if BETANO_USER and BETANO_PASS:
                    page.click("text=Login", timeout=5000)
                    time.sleep(2)
                    page.fill("input[name='username'], input[type='email']", BETANO_USER)
                    page.fill("input[name='password'], input[type='password']", BETANO_PASS)
                    page.click("button:has-text('Login'), button:has-text('Вход')")
                    time.sleep(8)
                    print("Login denendi paşam")
            except Exception as e:
                print(f"Login atlandı: {e}")

            # Aviator'a git
            page.goto("https://www.betano.bg/casino/live-casino/games/aviator/200078/", timeout=60000)
            time.sleep(15)
            print("Aviator sayfasında paşam, veri bekleniyor...")

            last_seen = None
            while True:
                try:
                    # Spribe geçmişini JS ile almaya çalış
                    content = page.content()
                    # 1.23x gibi oranları regex ile bul
                    matches = re.findall(r'(\d+\.\d{1,2})x', content)
                    if matches:
                        latest = matches[-1]
                        try:
                            val = float(latest)
                            if val!= last_seen and 1.0 < val < 1000:
                                last_seen = val
                                process_result(val)
                        except:
                            pass

                    # Alternatif: sayfadaki history elementleri
                    try:
                        elems = page.query_selector_all(".payout,.history-item, [class*='history']")
                        for el
