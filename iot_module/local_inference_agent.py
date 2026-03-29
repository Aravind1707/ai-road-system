import cv2
import os
import time
import json
import requests
from datetime import datetime

SERVER_URL = os.getenv('ROAD_AI_SERVER', 'http://localhost:8000/vehicle/infer')
SYNC_URL = os.getenv('ROAD_AI_SYNC_SERVER', 'http://localhost:8000/vehicle/offline/sync')
TOKEN = os.getenv('ROAD_AI_TOKEN', '')
CACHE_DIR = 'cache_frames'

os.makedirs(CACHE_DIR, exist_ok=True)


def push_frame(frame):
    _, encoded = cv2.imencode('.jpg', frame)
    if encoded is None:
        return False

    headers = {'Authorization': f'Bearer {TOKEN}'}
    files = {'file': ('frame.jpg', encoded.tobytes(), 'image/jpeg')}
    try:
        resp = requests.post(SERVER_URL, files=files, data={'vehicle_id': 'pi_cam'}, headers=headers, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def save_local(frame):
    filename = os.path.join(CACHE_DIR, f"frame_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.jpg")
    cv2.imwrite(filename, frame)
    return filename


def sync_cached():
    files = [f for f in os.listdir(CACHE_DIR) if f.lower().endswith('.jpg')]
    if not files:
        return 0

    payload = []
    for f in files:
        path = os.path.join(CACHE_DIR, f)
        with open(path, 'rb') as fp:
            image_bytes = fp.read()
            payload.append({'vehicle_id': 'pi_cam', 'image_bytes': image_bytes.hex()})

    try:
        res = requests.post(SYNC_URL, json=payload, headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}, timeout=15)
        if res.ok:
            for f in files:
                os.remove(os.path.join(CACHE_DIR, f))
            return len(files)
    except Exception:
        pass
    return 0


def live_stream(camera_index=0):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError('Camera not available')

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if not push_frame(frame):
            save_local(frame)

        synced = sync_cached()
        if synced > 0:
            print(f"Synced {synced} cached frames")

        time.sleep(0.2)

    cap.release()


if __name__ == '__main__':
    live_stream()
