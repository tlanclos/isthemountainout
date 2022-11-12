import json
import os
import io
import shutil
from datetime import date as Date
from datetime import datetime
from typing import Tuple, Dict, Iterator
from google.cloud import storage as gstorage
from urllib.parse import urlparse
from common.config import brand_filename, mountain_history_bucket_name, mountain_history_filename_template, classification_bucket_name, classification_filename
from common.storage import GcpBucketStorage
from io import BytesIO
import requests
from PIL import Image


class ImageProvider:
    def get(self) -> Tuple[Image.Image, datetime]:
        pass


class SpaceNeedleImageProvider(ImageProvider):
    cropped: bool

    def __init__(self, *, cropped: bool = True):
        self.cropped = cropped

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


class LatestSnapshotImageProvider(ImageProvider):
    storage: GcpBucketStorage

    def __latest_image_file(self) -> gstorage.Blob:
        blob = next(
            reversed(sorted(self.storage.list_files(''), key=self.__date_of_blob)))
        return blob, self.__date_of_blob(blob)

    def __date_of_blob(self, blob) -> datetime:
        return datetime.strptime(os.path.splitext(blob.name)[0], mountain_history_filename_template())

    def __init__(self):
        self.storage = GcpBucketStorage(
            bucket_name=mountain_history_bucket_name())

    def get(self) -> Tuple[Image.Image, Date]:
        image_blob, date = self.__latest_image_file()
        return Image.open(BytesIO(image_blob.download_as_bytes())), date


class Classification:
    classification: str
    mountainPosition: Tuple[float, float]


class DatasetImageProvider:
    storage: GcpBucketStorage
    image_storage: GcpBucketStorage
    classifications: Iterator[Tuple[str, Classification]]

    def __init__(self):
        self.storage = GcpBucketStorage(
            bucket_name=classification_bucket_name())
        self.image_storage = GcpBucketStorage(
            bucket_name=mountain_history_bucket_name())

    def __get_all_classifications(self) -> Dict[str, Classification]:
        return json.loads(self.storage.get(
            classification_filename()).download_as_string())

    def __iter__(self):
        self.classifications = iter(self.__get_all_classifications().items())
        return self

    def __next__(self) -> Tuple[str, str]:
        file_name, classification = next(self.classifications)
        return file_name, classification['classification']

    def get(self, filename) -> gstorage.Blob:
        return self.image_storage.get(filename)


class BrandImageProvider:
    storage: GcpBucketStorage

    def __init__(self):
        self.storage = GcpBucketStorage(
            bucket_name=classification_bucket_name())

    def get(self) -> Image.Image:
        blob = self.storage.get(os.path.join('v2', brand_filename()))
        blob.download_as_string()


class ImageEditor:
    image: Image

    def __init__(self, image: Image):
        self.image = image

    def crop(self, *, x: int, y: int, width: int, height: int):
        self.image = self.image.crop((x, y, x + width, y + height))
        return self

    def brand(self, *, brand: Image):
        self.image = self.__apply_brand(self.image, brand=brand)
        return self

    def __apply_brand(self, *, brand: Image):
        branded = self.image.copy()
        branded.paste(brand, (0, 0), brand)
        self.image = branded
        return self
