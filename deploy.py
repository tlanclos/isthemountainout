import argparse
import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Dict, List
from zipfile import ZipFile

from common.trainablemodel import generate_model, to_tflite

parser = argparse.ArgumentParser(description='Build packages for deployment')
parser.add_argument(
    'package', choices=['model', 'prod-package'], help='Which package to deploy')
args = parser.parse_args()


@dataclass
class DeploymentOptions:
    archive_name: str
    include_directories: List[str]
    include_files: Dict[str, str]
    weights: str


def list_files(startpath):
    for root, _, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))


def deploy_package(options: DeploymentOptions):
    with tempfile.TemporaryDirectory() as dirname:
        for filename, newname in options.include_files.items():
            newpath = os.path.join(
                dirname, newname if newname else os.path.basename(filename))
            print(f'copying {filename} -> {newpath}')
            shutil.copyfile(filename, newpath)

        for directory in options.include_directories:
            newpath = os.path.join(
                dirname, os.path.basename(directory))
            print(f'copying {directory} -> {newpath}')
            shutil.copytree(directory, newpath)

        deploy_zip_filepath = os.path.join(
            'deploy', f'{options.archive_name}.zip')
        os.makedirs(os.path.dirname(deploy_zip_filepath), exist_ok=True)

        with ZipFile(deploy_zip_filepath, 'w') as f:
            for folder_name, _, filenames in os.walk(dirname):
                for filename in filenames:
                    file_path = os.path.join(folder_name, filename)
                    newpath = os.path.relpath(file_path, dirname)
                    print(f'writing {file_path} -> {newpath}')
                    f.write(file_path, newpath)


if args.package == 'prod-package':
    deploy_package(DeploymentOptions(
        archive_name='prod',
        include_directories=['common'],
        include_files={
            'snapshot.py': 'snapshot.py',
            'classify.py': 'classify.py',
            'requirements.prod.txt': 'requirements.txt',
        },
        weights=os.path.join('resources', 'weights.h5')
    ))
elif args.package == 'model':
    weights_path = os.path.join('resources', 'weights.h5')
    model_path = os.path.join('deploy', 'model.tflite')
    print(
        f'generating tflite model for weights {weights_path} -> {model_path}')
    with open(model_path, 'wb') as f:
        f.write(to_tflite(generate_model(weights_filepath=weights_path)))
