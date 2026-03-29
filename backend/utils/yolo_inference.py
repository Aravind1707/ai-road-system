from ultralytics import YOLO
from PIL import Image
import io

MODEL_PATH = "yolov8n.pt"

_model = None

def get_model():
    global _model
    if _model is None:
        _model = YOLO(MODEL_PATH)
    return _model


def infer_image_bytes(image_bytes: bytes):
    model = get_model()
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    results = model(img)
    processed = []
    for r in results:
        for box in r.boxes:
            processed.append({
                'x1': float(box.xyxy[0][0]),
                'y1': float(box.xyxy[0][1]),
                'x2': float(box.xyxy[0][2]),
                'y2': float(box.xyxy[0][3]),
                'confidence': float(box.conf[0]),
                'class': int(box.cls[0])
            })
    return processed


def annotate_video(input_path: str, output_path: str, model_arch: str = None):
    import cv2

    model = get_model() if model_arch is None else YOLO(model_arch)
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 20.0

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        if len(results) > 0:
            annot = results[0].plot()
            writer.write(annot)
        else:
            writer.write(frame)

    cap.release()
    writer.release()
    return output_path

