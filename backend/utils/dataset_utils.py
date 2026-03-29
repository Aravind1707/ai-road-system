import os
import requests
import zipfile
import tarfile
from pathlib import Path

DATASETS = [
    {
        'name': 'Road Damage Detection Dataset (Japan)',
        'url': 'https://zenodo.org/record/2532565/files/RoadDamageDataset.zip',
        'type': 'road_damage',
        'description': 'Labeled pothole/crack dataset for road condition detection',
        'license': 'CC BY 4.0'
    },
    {
        'name': 'BDD100K',
        'url': 'https://bj.bcebos.com/bdd100k/bdd100k_images_100k.zip',
        'type': 'traffic',
        'description': 'Street scenes for multi-weather object detection',
        'license': 'CC BY 4.0'
    },
    {
        'name': 'Cityscapes',
        'url': 'https://www.cityscapes-dataset.com/',
        'type': 'road',
        'description': 'Urban street scene dataset for road, lane, and vehicle detection',
        'license': 'CC BY-NC-SA 4.0'
    },
    {
        'name': 'Mapillary Vistas (public subset)',
        'url': 'https://registry.opendata.aws/mapillary/',
        'type': 'road',
        'description': 'High-resolution street-level images, road segmentation',
        'license': 'CC BY-SA 4.0'
    },
    {
        'name': 'COCO',
        'url': 'https://cocodataset.org/#download',
        'type': 'generic',
        'description': 'General object detection with traffic objects for transfer learning',
        'license': 'CC BY 4.0'
    },
    {
        'name': 'OpenImages',
        'url': 'https://storage.googleapis.com/openimages/web/index.html',
        'type': 'generic',
        'description': 'Large-scale image dataset with road, vehicle, and object classes',
        'license': 'CC BY 4.0'
    },
    {
        'name': 'Kaggle Indian Road Damage Datasets',
        'url': 'https://www.kaggle.com/datasets?search=india+road+damage',
        'type': 'road_damage',
        'description': 'Local Indian pothole and road crack datasets for domain-specific tuning',
        'license': 'varies'
    },
    {
        'name': 'Kaggle Pothole Detection Datasets',
        'url': 'https://www.kaggle.com/datasets?search=pothole',
        'type': 'road_damage',
        'description': 'Kaggle collections of pothole and road distress detection images',
        'license': 'varies'
    }
]


def _extract_archive(path: str, dest: str):
    if path.endswith('.zip'):
        with zipfile.ZipFile(path, 'r') as z:
            z.extractall(dest)
    elif path.endswith(('.tar.gz', '.tgz', '.tar')):
        with tarfile.open(path, 'r:*') as t:
            t.extractall(dest)


def download_dataset(dataset_name: str, dest_path: str = 'data/datasets') -> str:
    dataset = next((d for d in DATASETS if d['name'] == dataset_name), None)
    if dataset is None:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    os.makedirs(dest_path, exist_ok=True)
    output_file = os.path.join(dest_path, os.path.basename(dataset['url']))

    # Some datasets require manual auth or download pages; these cannot be downloaded automatically.
    manual_download = [
        'Mapillary Vistas (public subset)',
        'COCO',
        'Cityscapes',
        'OpenImages',
        'Kaggle Indian Road Damage Datasets',
        'Kaggle Pothole Detection Datasets'
    ]
    if dataset['name'] in manual_download:
        raise RuntimeError(f"Manual download needed, see {dataset['url']}")

    if os.path.exists(output_file):
        return output_file

    resp = requests.get(dataset['url'], stream=True, timeout=60)
    resp.raise_for_status()
    with open(output_file, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    _extract_archive(output_file, dest_path)
    return output_file


def list_datasets():
    return DATASETS
