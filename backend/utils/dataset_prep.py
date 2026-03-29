import csv
import os
import random
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from PIL import Image

CLASS_NAMES = ['pothole', 'longitudinal_crack', 'lat_crack', 'alligator_crack']
CLASS_NAME_TO_ID = {name: idx for idx, name in enumerate(CLASS_NAMES)}
DEFAULT_DAMAGE_TYPE_MAP = {
    'D00': 'longitudinal_crack',
    'D01': 'lat_crack',
    'D10': 'alligator_crack',
    'D40': 'pothole',
}


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def save_yolo_data_yaml(output_path: Path, train_dir: Path, val_dir: Path, names: List[str]):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = [
        f'train: {train_dir.as_posix()}',
        f'val: {val_dir.as_posix()}',
        f'nc: {len(names)}',
        'names: [' + ', '.join(f"'{name}'" for name in names) + ']',
    ]
    output_path.write_text('\n'.join(content) + '\n', encoding='utf-8')
    return output_path


def _choose_field(fields: List[str], candidates: Iterable[str]) -> Optional[str]:
    for candidate in candidates:
        for field in fields:
            if field.lower() == candidate.lower():
                return field
    return None


def _normalize_bbox(xmin: float, ymin: float, xmax: float, ymax: float, img_w: int, img_h: int) -> Tuple[float, float, float, float]:
    x_center = (xmin + xmax) / 2.0 / img_w
    y_center = (ymin + ymax) / 2.0 / img_h
    width = (xmax - xmin) / img_w
    height = (ymax - ymin) / img_h
    return x_center, y_center, width, height


def _resolve_class_id(label_value: str, class_map: Optional[Dict[str, str]] = None) -> Optional[int]:
    if label_value is None:
        return None
    label_value = str(label_value).strip()
    if label_value == '':
        return None
    if label_value.isdigit():
        idx = int(label_value)
        return idx if idx >= 0 and idx < len(CLASS_NAMES) else None
    normalized = label_value.upper()
    if class_map and normalized in class_map:
        mapped_name = class_map[normalized]
        return CLASS_NAME_TO_ID.get(mapped_name)
    if normalized in CLASS_NAME_TO_ID:
        return CLASS_NAME_TO_ID[normalized]
    return None


def load_csv_annotations(csv_path: Path, class_map: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    rows = []
    with csv_path.open(newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rows.append(row)
    return rows


def _find_image_column(fields: List[str]) -> Optional[str]:
    return _choose_field(fields, ['image', 'filename', 'file', 'image_name', 'file_name', 'img'])


def _find_bbox_columns(fields: List[str]) -> Optional[Tuple[str, str, str, str]]:
    x1 = _choose_field(fields, ['x1', 'xmin', 'left'])
    y1 = _choose_field(fields, ['y1', 'ymin', 'top'])
    x2 = _choose_field(fields, ['x2', 'xmax', 'right'])
    y2 = _choose_field(fields, ['y2', 'ymax', 'bottom'])
    if x1 and y1 and x2 and y2:
        return x1, y1, x2, y2
    return None


def _find_class_column(fields: List[str]) -> Optional[str]:
    return _choose_field(fields, ['class', 'label', 'category', 'damage_type', 'type'])


def write_yolo_label(label_path: Path, image_path: Path, annotations: List[Dict[str, str]], class_map: Optional[Dict[str, str]] = None):
    with Image.open(image_path) as img:
        img_w, img_h = img.size
    lines: List[str] = []
    for ann in annotations:
        fields = list(ann.keys())
        bbox_fields = _find_bbox_columns(fields)
        class_field = _find_class_column(fields)
        if bbox_fields is None or class_field is None:
            continue
        x1 = float(ann[bbox_fields[0]])
        y1 = float(ann[bbox_fields[1]])
        x2 = float(ann[bbox_fields[2]])
        y2 = float(ann[bbox_fields[3]])
        class_id = _resolve_class_id(ann[class_field], class_map=class_map)
        if class_id is None:
            continue
        x_center, y_center, width, height = _normalize_bbox(x1, y1, x2, y2, img_w, img_h)
        if width <= 0 or height <= 0:
            continue
        lines.append(f'{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}')
    if lines:
        label_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def prepare_yolo_dataset_from_csv(
    csv_path: str,
    image_root: str,
    output_root: str = 'data/yolo',
    val_ratio: float = 0.2,
    class_map: Optional[Dict[str, str]] = None,
    seed: int = 42,
):
    csv_path = Path(csv_path)
    image_root = Path(image_root)
    output_root = Path(output_root)

    class_map = class_map or DEFAULT_DAMAGE_TYPE_MAP
    rows = load_csv_annotations(csv_path, class_map=class_map)
    if not rows:
        raise ValueError(f'No rows found in {csv_path}')

    image_col = _find_image_column(list(rows[0].keys()))
    bbox_cols = _find_bbox_columns(list(rows[0].keys()))
    class_col = _find_class_column(list(rows[0].keys()))
    if image_col is None or bbox_cols is None or class_col is None:
        raise ValueError('CSV must contain image, bbox, and class columns')

    grouped: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        image_name = row[image_col].strip()
        grouped.setdefault(image_name, []).append(row)

    image_names = list(grouped.keys())
    random.Random(seed).shuffle(image_names)
    val_count = int(len(image_names) * val_ratio)
    val_names = set(image_names[:val_count])
    train_names = image_names[val_count:]

    for split, names in [('train', train_names), ('val', val_names)]:
        img_dest = output_root / split / 'images'
        lbl_dest = output_root / split / 'labels'
        ensure_dir(img_dest)
        ensure_dir(lbl_dest)
        for name in names:
            image_path = image_root / name
            if not image_path.exists():
                continue
            dest_img_path = img_dest / name
            ensure_dir(dest_img_path.parent)
            shutil.copy2(image_path, dest_img_path)
            label_path = lbl_dest / (Path(name).stem + '.txt')
            write_yolo_label(label_path, image_path, grouped[name], class_map=class_map)

    save_yolo_data_yaml(
        output_path=output_root / 'data.yaml',
        train_dir=output_root / 'train',
        val_dir=output_root / 'val',
        names=CLASS_NAMES,
    )
    return output_root / 'data.yaml'


def split_existing_yolo_dataset(
    image_dir: str,
    label_dir: str,
    output_root: str = 'data/yolo',
    val_ratio: float = 0.2,
    seed: int = 42,
):
    image_dir = Path(image_dir)
    label_dir = Path(label_dir)
    output_root = Path(output_root)

    image_paths = sorted(image_dir.rglob('*.*'))
    image_paths = [p for p in image_paths if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}]
    matched = []
    for image_path in image_paths:
        label_path = label_dir / (image_path.stem + '.txt')
        if label_path.exists():
            matched.append((image_path, label_path))

    if not matched:
        raise ValueError('No matching YOLO labels found for images in the provided directories.')

    random.Random(seed).shuffle(matched)
    val_count = int(len(matched) * val_ratio)
    splits = {'val': matched[:val_count], 'train': matched[val_count:]}

    for split_name, entries in splits.items():
        img_dest = output_root / split_name / 'images'
        lbl_dest = output_root / split_name / 'labels'
        ensure_dir(img_dest)
        ensure_dir(lbl_dest)
        for image_path, label_path in entries:
            rel = image_path.relative_to(image_dir)
            target_image = img_dest / rel
            ensure_dir(target_image.parent)
            shutil.copy2(image_path, target_image)
            target_label = lbl_dest / (rel.stem + '.txt')
            ensure_dir(target_label.parent)
            shutil.copy2(label_path, target_label)

    save_yolo_data_yaml(
        output_path=output_root / 'data.yaml',
        train_dir=output_root / 'train',
        val_dir=output_root / 'val',
        names=CLASS_NAMES,
    )
    return output_root / 'data.yaml'
