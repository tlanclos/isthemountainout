import os
import io
import shutil
from datetime import date as Date
from datetime import datetime
from typing import Tuple
from google.cloud import storage as gstorage
from urllib.parse import urlparse
from common.config import mountain_history_bucket_name, mountain_history_filename_template
from common.storage import GcpBucketStorage
from io import BytesIO
import requests
from PIL import Image


class ImageProvider:
    def get(self) -> Tuple[Image.Image, datetime]:
        pass


class SpaceNeedleImageProvider(ImageProvider):
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
            return image.resize((int(width / scale), int(height / scale))), date
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


def crop(image: Image, *, x: int, y: int, width: int, height: int) -> Image:
    return image.crop((x, y, x + width, y + height))
