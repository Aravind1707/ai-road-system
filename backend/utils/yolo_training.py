from ultralytics import YOLO
import os


def train_yolo_model(data_dir: str, output_dir: str = 'runs/train', model_arch: str = 'yolov10n.pt', epochs: int = 80, imgsz: int = 640):
    """Train YOLO model in YOLOv10/YOLOv8 format on a custom dataset."""
    # Supports dynamic choice: yolov8n.pt, yolov10n.pt, etc.
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"data_dir not found: {data_dir}")

    # Fallback to yolov8n if yolov10 weights unavailable
    model_path = model_arch if os.path.exists(model_arch) else 'yolov8n.pt'

    model = YOLO(model_path)
    results = model.train(
        data=data_dir,
        epochs=epochs,
        imgsz=imgsz,
        project=output_dir,
        name='road_damage',
        cache=True
    )
    return results


def evaluate_yolo_model(weights_path: str, data_dir: str):
    model = YOLO(weights_path)
    metrics = model.val(data=data_dir)
    return metrics

