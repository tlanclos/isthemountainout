import os
import shutil
import tempfile
from zipfile import ZipFile
import argparse
from typing import List, Dict

parser = argparse.ArgumentParser(description='Build packages for deployment')
parser.add_argument('package', choices=['snapshot'], help='Package to build')

args = parser.parse_args()


class DeploymentOptions:
    archive_name: str
    include_directories: List[str]
    include_files: Dict[str, str]

    def __init__(self, *, archive_name: str, include_directories: List[str], include_files: Dict[str, str]):
        self.archive_name = archive_name
        self.include_directories = include_directories
        self.include_files = include_files


def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
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

        with ZipFile(os.path.join('deploy', f'{options.archive_name}.zip'), 'w') as f:
            for folder_name, _, filenames in os.walk(dirname):
                for filename in filenames:
                    file_path = os.path.join(folder_name, filename)
                    newpath = os.path.relpath(file_path, dirname)
                    print(f'writing {file_path} -> {newpath}')
                    f.write(file_path, newpath)


if args.package == 'snapshot':
    deploy_package(DeploymentOptions(
        archive_name='snapshot',
        include_directories=['common'],
        include_files={
            'snapshot.py': 'main.py',
            'requirements.snapshot.txt': 'requirements.txt',
        },
    ))
else:
    print(f'Unknown package {args.package}')
