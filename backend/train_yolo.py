import argparse
from pathlib import Path

from utils.dataset_prep import CLASS_NAMES, save_yolo_data_yaml
from utils.yolo_training import train_yolo_model


def main():
    parser = argparse.ArgumentParser(description='Train YOLOv10 on prepared dataset')
    parser.add_argument('--data', type=str, default='data/yolo/data.yaml', help='YOLO data.yaml path or dataset root folder')
    parser.add_argument('--model', type=str, default='yolov10n.pt', help='YOLO model weights or config to start from')
    parser.add_argument('--epochs', type=int, default=80, help='Number of training epochs')
    parser.add_argument('--imgsz', type=int, default=640, help='Image size for training')
    parser.add_argument('--output', type=str, default='runs/train', help='YOLO training output directory')
    parser.add_argument('--create-data-yaml', action='store_true', help='Create default data.yaml if data is a folder')
    parser.add_argument('--train-dir', type=str, default='data/yolo/train', help='Train images/labels directory used when creating data.yaml')
    parser.add_argument('--val-dir', type=str, default='data/yolo/val', help='Validation images/labels directory used when creating data.yaml')
    args = parser.parse_args()

    data_path = Path(args.data)
    if args.create_data_yaml and data_path.is_dir():
        data_yaml = data_path / 'data.yaml'
        if not data_yaml.exists():
            save_yolo_data_yaml(
                output_path=data_yaml,
                train_dir=Path(args.train_dir),
                val_dir=Path(args.val_dir),
                names=CLASS_NAMES,
            )
            print(f'Created data.yaml at {data_yaml}')
        data_path = data_yaml

    print(f'Starting YOLOv10 training with model={args.model}, data={data_path}')
    train_yolo_model(
        data_dir=str(data_path),
        output_dir=args.output,
        model_arch=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
    )


if __name__ == '__main__':
    main()
