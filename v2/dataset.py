import os
import shutil
import tempfile
from zipfile import ZipFile
from datetime import datetime
from common.image import DatasetImageProvider
import argparse

parser = argparse.ArgumentParser(
    description='Utility for performing actions on dataset')
parser.add_argument('action', choices=[
                    'download'], help='Action to perform on dataset')

args = parser.parse_args()


def download_dataset():
    provider = DatasetImageProvider()
    now = datetime.now()
    os.makedirs('dataset', exist_ok=True)
    with ZipFile(os.path.join('dataset', f'dataset-{now.strftime("%Y-%m-%dT%H-%M-%S")}.zip'), 'w') as f:
        for file_name, classification in provider:
            newpath = os.path.join(classification, file_name)
            print(f'writing {file_name} -> {newpath}')
            f.writestr(newpath, provider.get(file_name).download_as_bytes())


if args.action == 'download':
    download_dataset()
else:
    print(f'Unknown action {args.action}')
