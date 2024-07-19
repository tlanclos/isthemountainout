import os
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import List

from PIL import Image

from common.const import mountain_history_filename_template


class File:
    def filename(self) -> str:
        raise NotImplementedError()

    def read(self) -> bytes:
        raise NotImplementedError()

    def date(self) -> datetime:
        return datetime.strptime(
            os.path.splitext(self.filename())[0],
            mountain_history_filename_template())

    def as_image(self) -> Image.Image:
        return Image.open(BytesIO(self.read()))


@dataclass
class LocalFile(File):
    filepath: str

    def filename(self) -> str:
        return os.path.basename(self.filepath)

    def read(self) -> bytes:
        with open(self.filepath, 'rb') as f:
            return f.read()


class Storage:
    def save_image(self, image: Image.Image, *, filename: str):
        raise NotImplementedError()

    def list_files(self, directory: str) -> List[File]:
        raise NotImplementedError()

    def get(self, filename: str) -> File:
        raise NotImplementedError()

    def get_image(self, filename: str) -> Image.Image:
        return self.get(filename).as_image()


@dataclass
class LocalFileStorage(Storage):
    base_path: str

    def save_image(self, image: Image.Image, *, filename: str):
        with open(os.path.join(self.base_path, f'{filename}.png'), 'wb') as f:
            image.save(f, format='PNG')

    def list_files(self, directory: str) -> List[File]:
        listing_directory = os.path.join(self.base_path, directory)
        return [
            LocalFile(filepath=os.path.join(listing_directory, filename)) for filename in os.listdir(listing_directory)
        ]

    def get(self, filename: str) -> File:
        return LocalFile(filepath=os.path.join(self.base_path, filename))
