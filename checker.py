import threading
import requests
import random
import time
import signal
import sys
from queue import Queue, Empty
from itertools import product

WEBHOOK_URL = "YOUR_WEBHOOK"
GIF_URL = "https://c.tenor.com/osEG_d75PFMAAAAC/tenor.gif"
THREADS = 5

API_ENDPOINTS = [
    "https://discord.com/api/v9/unique-username/username-attempt-unauthed",
    "https://canary.discord.com/api/v9/unique-username/username-attempt-unauthed"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]


CHARS = "abcdefghijklmnopqrstuvwxyz0123456789._"
usernames = ["".join(x) for x in product(CHARS, repeat=3)]
random.shuffle(usernames)

queue = Queue()
for u in usernames:
    queue.put(u)

TOTAL = len(usernames)


checked = 0
found = set()
lock = threading.Lock()
running = True


def send_webhook(payload):
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"[!] Webhook hatası: {e}")

def bot_started():
    send_webhook({
        "username": " :( ",
        "embeds": [{
            "title": "🟢 SYSTEM ONLINE",
            "fields": [
                {"name": "Durum", "value": "Username Checker Online", "inline": False},
                {"name": "Toplam", "value": f"{TOTAL:,}", "inline": True},
                {"name": "Thread", "value": f"{THREADS}", "inline": True}
            ],
            "color": 0x2ECC71,
            "image": {"url": GIF_URL},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }]
    })

def bot_stopped():
    send_webhook({
        "username": " :( ",
        "embeds": [{
            "title": "🔴 SYSTEM OFFLINE",
            "fields": [
                {"name": "Kontrol Edilen", "value": f"{checked:,}", "inline": False}
            ],
            "color": 0xE74C3C,
            "image": {"url": GIF_URL},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }]
    })

#                               NICKNAME HIT WEBHOOK 
def send_found(username):
    send_webhook({
        "username": " :( ",
        "content": "@everyone",
        "embeds": [{
            "description": (
                "• **Username Checked**\n"
                f"• **Nickname :** `{username}`\n\n"
                f"Made by Hotwing • {time.strftime('%d.%m.%Y %H:%M:%S')}"
            ),
            "color": 0x0F0F14,
            "thumbnail": {
                "url": "https://i.imgur.com/6XKQp4E.png"
            }
        }]
    })


def worker():
    global checked
    session = requests.Session()

    while running:
        try:
            username = queue.get(timeout=1)
        except Empty:
            continue

        with lock:
            checked += 1
            print(f"[CHECK {checked:,}/{TOTAL:,}] @{username}")

        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Content-Type": "application/json"
        }

        try:
            r = session.post(
                random.choice(API_ENDPOINTS),
                json={"username": username},
                headers=headers,
                timeout=8
            )

            if '"taken":false' in r.text:
                with lock:
                    if username not in found:
                        found.add(username)
                        print(f"[AVAILABLE] @{username}")
                        send_found(username)

            elif r.status_code == 429:
                time.sleep(1)
                queue.put(username)

        except Exception as e:
            print(f"[ERROR] @{username} -> {e}")
            queue.put(username)

        finally:
            queue.task_done()


def shutdown(sig, frame):
    global running
    running = False
    print("\n[!] Bot kapatılıyor...")
    bot_stopped()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)

print(f"[+] {TOTAL:,} username yüklendi")
print("[*] Hotwing iyi uçuşlar diler")
print("[*] Ctrl + C ile durdurursun\n")

bot_started()

for _ in range(THREADS):
    threading.Thread(target=worker, daemon=True).start()

while True:
    time.sleep(1)
