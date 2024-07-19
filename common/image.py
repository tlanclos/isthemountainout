import io
import shutil
from bisect import bisect
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime
from typing import Dict, Iterator, Tuple
from urllib.parse import urlparse

import requests
from PIL import Image

from common.storage import File, Storage


def __max_image_size(pixels: int):
    return DecompressionBombIgnorer(max_image_size=pixels)


@dataclass
class DecompressionBombIgnorer:
    max_image_size: int
    _current_max_image_size: Optional[int] = None

    def __enter__(self):
        self._current_max_image_size = Image.MAX_IMAGE_PIXELS
        Image.MAX_IMAGE_PIXELS = self.max_image_size
        return None

    def __exit__(self, exc_type, exc_value, exc_tb):
        Image.MAX_IMAGE_PIXELS = self._current_max_image_size


class ImageProvider:
    def get(self) -> Tuple[Image.Image, datetime]:
        pass


@dataclass
class SpaceNeedleImageProvider(ImageProvider):
    cropped: bool = True

    def __space_needle_url(self) -> str:
        return 'https://backend.roundshot.com/cams/241/original'

    def get(self) -> Tuple[Image.Image, datetime]:
        url = self.__space_needle_url()
        redirected_url = requests.head(url, allow_redirects=True).url
        # Example format: https://storage.roundshot.com/544a1a9d451563.40343637/2021-07-02/14-40-00/2021-07-02-14-40-00_original.jpg
        url = urlparse(redirected_url)
        url_path = list(filter(None, url.path.split('/')))
        date = datetime.strptime(
            f'{url_path[1]}T{url_path[2]}', '%Y-%m-%dT%H-%M-%S')
        req = requests.get(redirected_url, stream=True)
        if req.status_code == 200:
            req.raw.decode_content = True
            data = io.BytesIO()
            shutil.copyfileobj(req.raw, data)
            data.seek(0)
            with __max_image_size(200_000_000):
                image = Image.open(data)
            width, height = image.size
            # The original image size had a height of 2048, so try to keep it within those bounds keeping the aspect ratio
            scale = height / 2048
            resized = image.resize((int(width / scale), int(height / scale)))
            if self.cropped:
                resized = ImageEditor(resized).crop(
                    x=7036, y=162, width=1920, height=1080).image
            return resized, date
        else:
            raise IOError(
                f'Could not download latest image from {url} -> {redirected_url}', req)


@dataclass
class LatestSnapshotImageProvider(ImageProvider):
    storage: Storage

    def _image_file(self) -> File:
        return next(reversed(sorted(self.storage.list_files('.'), key=lambda f: f.date())))

    def get(self) -> Tuple[Image.Image, Date]:
        image_file = self._image_file()
        return image_file.as_image(), image_file.date()


@dataclass
class TimestampedSnapshotImageProvider(LatestSnapshotImageProvider):
    timestamp: datetime

    def _image_file(self) -> File:
        files = list(
            sorted(self.storage.list_files('.'), key=lambda f: f.date()))
        timestamps = [file.date() for file in files]
        index = max(0, min(len(timestamps) - 1,
                    bisect(timestamps, self.timestamp)))
        return files[index]


class Classification:
    classification: str
    mountainPosition: Tuple[float, float]


class DatasetImageProvider:
    snapshots: Storage
    classifications: Dict[str, Classification]
    _classifications_iterator: Iterator[Tuple[str, Classification]]

    def __init__(self, *, snapshots: Storage, classifications: Dict[str, Classification]):
        self.snapshots = snapshots
        self.classifications = classifications

    def __iter__(self):
        self._classifications_iterator = iter(self.classifications.items())
        return self

    def __next__(self) -> Tuple[str, str]:
        file_name, classification = next(self._classifications_iterator)
        return file_name, classification['classification']

    def get(self, filename) -> File:
        return self.snapshots.get(filename)


class ConstantImageProvider(ImageProvider):
    file: File

    def __init__(self, *, file: File):
        self.file = file

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(file={self.file})'

    def get(self) -> Image.Image:
        return self.file.as_image()


class ImageEditor:
    image: Image

    def __init__(self, image: Image):
        self.image = image

    def crop(self, *, x: int, y: int, width: int, height: int):
        self.image = self.image.crop((x, y, x + width, y + height))
        return self

    def brand(self, *, brand: Image):
        self.image = self.__apply_brand(brand=brand)
        return self

    def __apply_brand(self, *, brand: Image):
        branded = self.image.copy()
        branded.paste(brand, (0, 0), brand)
        self.image = branded
        return self
