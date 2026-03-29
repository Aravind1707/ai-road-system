import json
import os
import requests
from datetime import datetime

CACHE_FILE = 'offline_cache.json'
SERVER_URL = os.getenv('ROAD_AI_SERVER', 'http://localhost:8000/vehicle/upload')
TOKEN = os.getenv('ROAD_AI_TOKEN', '')


def save_offline(data):
    existing = []
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as fp:
            existing = json.load(fp)

    existing.append({'timestamp': datetime.utcnow().isoformat(), 'data': data})
    with open(CACHE_FILE, 'w') as fp:
        json.dump(existing, fp)


def sync():
    if not os.path.exists(CACHE_FILE):
        return 0

    with open(CACHE_FILE, 'r') as fp:
        queue = json.load(fp)

    if not queue:
        return 0

    success_items = []
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    for item in queue:
        payload = item['data']
        try:
            res = requests.post(SERVER_URL, json=payload, headers=headers, timeout=6)
            if res.status_code == 200:
                success_items.append(item)
        except Exception:
            continue

    if success_items:
        remaining = [i for i in queue if i not in success_items]
        with open(CACHE_FILE, 'w') as fp:
            json.dump(remaining, fp)

    return len(success_items)


if __name__ == '__main__':
    # daily sync cycle or manual agent command
    synced = sync()
    print(f"Synced {synced} offline entries.")
