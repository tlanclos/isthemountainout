import argparse
import os
from datetime import datetime
from zipfile import ZipFile

from common.image import DatasetImageProvider

parser = argparse.ArgumentParser(
    description='Utility for performing actions on dataset')
parser.add_argument('action', choices=[
                    'download'], help='Action to perform on dataset')

args = parser.parse_args()


# TODO: Need to refactor this to work with the "storage" version of the DatasetImageProvider
# TODO: Will need to create a network provided version or just add a configuration in the
# TODO: Jupyter script to load from the right directory
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
