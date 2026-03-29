# AI Road System

Fleet-Based Intelligent Road Monitoring and Repair Management System

## Backend

1. Install dependencies

```bash
cd /workspaces/ai-road-system
python3 -m pip install -r requirements.txt
```

2. Start PostgreSQL with database `road_ai` and user `postgres`.

### Enable PostGIS extension

In psql or pgAdmin connected to road_ai:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

3. Add `postgis` to your PostGIS enabled database and set `DATABASE_URL` in `backend/config.py`.

3. Update `backend/database.py` DB URL

```python
DATABASE_URL = "postgresql://postgres:admin123@localhost:5432/road_ai"
```

4. Run server

```bash
cd /workspaces/ai-road-system/backend
uvicorn main:app --reload --port 8000
```

5. Open docs:

`http://127.0.0.1:8000/docs`

## Frontend

1. Install node modules:

```bash
cd /workspaces/ai-road-system/frontend
npm install
```

2. Run:

```bash
npm run dev
```

3. Open Vite URL (e.g., `http://127.0.0.1:5173`)

## Deployment options

### Docker Compose

```bash
docker-compose up --build
```

### Kubernetes

```bash
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

### Cloud (AWS/GCP)

- AWS: EKS + RDS + S3.
- GCP: GKE + Cloud SQL + Cloud Storage.
- Use secrets for JWT secret and SMTP credentials.

## Testing

### Pytest

```bash
cd backend
pytest -q
```

### Cypress

```bash
cd frontend
npx cypress open
```

## API endpoints

- `POST /auth/register?username=<name>&password=<pass>&role=<role>`
- `POST /auth/login?username=<name>&password=<pass>`
- `POST /auth/refresh` (body: `token`)
- `POST /vehicle/upload` (secure; requires `Authorization: Bearer <access_token>`)
- `POST /vehicle/infer` (file upload, requires auth)
- `POST /vehicle/offline/sync` (batch upload from edge device; requires auth)
- `GET /vehicle/segment/{segment_id}`
- `GET /predict/segment/{segment_id}`
- `GET /vehicle/routes/{vehicle_id}`
- `GET /route/{route_id}/points`
- `GET /vehicle/complaints`
- `POST /vehicle/complaints/{complaint_id}/send`
- `GET /vehicle/complaints/{complaint_id}/pdf` (manager/admin)
- `PATCH /vehicle/complaints/{complaint_id}`
- `GET /audit?status=<>&source=<>&event_type=<>` (admin/manager)

## New Features (2026)

- Integrated YOLOv8/YOLOv10-compatible detection pipeline via `backend/utils/yolo_inference.py` and `backend/routes/vehicle.py`.
- Autonomous model-training endpoint in `backend/routes/vehicle.py`: `/vehicle/train-yolo` and `/vehicle/eval-yolo`.
- Live video inference endpoint: `/vehicle/infer/video` (MP4 upload + annotated MP4 output).
- Enhanced Road Damage Index (RDI) in `backend/utils/damage.py` with vibration, road type, traffic density.
- LSTM-based trend prediction in `backend/utils/lstm_trend.py` and `/predict/segment/{segment_id}`.
- Government reporting adapter in `backend/utils/gov_api.py` and `/vehicle/complaints/{complaint_id}/send`.
- Automated complaint PDF generation in `backend/utils/report.py` and `/vehicle/complaints/{complaint_id}/pdf`.
- Edge offline sync agent in `iot_module/offline_sync_agent.py` and `/vehicle/offline/sync`.
- Audit logging fully applied to every critical event in `backend/utils/audit.py` and `/audit` route.

## Suggested datasets for high accuracy road damage model

- Road Damage Dataset (Japan) - with damage categories, day/night, 5120 images: https://zenodo.org/record/2532565/files/RoadDamageDataset.zip
- BDD100K (traffic / object detection / camera pose): https://bdd-data.berkeley.edu
- Cityscapes (urban street scene detection): https://www.cityscapes-dataset.com/
- Mapillary Vistas (road infrastructure) — use public subset evaluated for roads: https://www.mapillary.com/dataset/vistas
- OpenImages (road and vehicle image classes): https://storage.googleapis.com/openimages/web/index.html
- Kaggle Indian Road Damage / Pothole Datasets search: https://www.kaggle.com/datasets?search=india+road+damage
- Kaggle Pothole Detection Datasets search: https://www.kaggle.com/datasets?search=pothole
- Custom local field data (camera-mounted Pi dataset) using this project data format.

## Dataset tooling

- `backend/utils/dataset_utils.py` has `list_datasets()` and `download_dataset(dataset_name)`.
- `backend/utils/dataset_prep.py` provides helpers for:
  - creating YOLO `data.yaml`
  - converting CSV-style road damage annotations into YOLO labels
  - splitting images/labels into `train/val`
- Put `train/val/images`, `train/val/labels` in the same root dataset path and specify in config YAML for YOLO training.

## YOLOv10 training

1. Prepare your dataset in YOLO format under `data/yolo/train` and `data/yolo/val`.
2. Create or regenerate `data/yolo/data.yaml` with the repo helper:
   ```bash
   cd /workspaces/ai-road-system/backend
   python train_yolo.py --data data/yolo --create-data-yaml
   ```
3. Start training on YOLOv10:
   ```bash
   cd /workspaces/ai-road-system/backend
   python train_yolo.py --data data/yolo/data.yaml --model yolov10n.pt --epochs 80 --imgsz 640 --output runs/train
   ```
4. Use the trained weights from `runs/train/road_damage/weights/best.pt` for inference in the app.

## Offline mode + Pi live camera pipeline

1. On Pi, run `iot_module/offline_sync_agent.py` (caches JSON when offline).
2. Provide `/vehicle/infer` for photo and `/vehicle/infer/video` for MP4 video inference.
3. If offline, treat inference locally on Pi and sync to central when internet is back.
4. For live camera stream, run local process:
   - capture camera frames via OpenCV or GStreamer
   - call `infer_image_bytes` locally or send compressed frame to `/vehicle/infer`
   - if server unreachable, queue frames to offline cache using same pattern as `offline_sync_agent.py`


