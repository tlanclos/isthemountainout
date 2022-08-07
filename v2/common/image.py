import io
import shutil
from datetime import date as Date
from datetime import datetime
from typing import Tuple
from urllib.parse import urlparse

import requests
from PIL import Image


class ImageProvider:
    def get(self) -> Tuple[Image.Image, Date]:
        pass


class SpaceNeedleImageProvider(ImageProvider):
    def __space_needle_url(self) -> str:
        return 'https://backend.roundshot.com/cams/241/original'

    def get(self) -> Tuple[Image.Image, Date]:
        url = self.__space_needle_url()
        redirected_url = requests.head(url, allow_redirects=True).url
        # Example format: https://storage.roundshot.com/544a1a9d451563.40343637/2021-07-02/14-40-00/2021-07-02-14-40-00_original.jpg
        date = datetime.fromisoformat(
            list(filter(None, urlparse(redirected_url).path.split('/')))[1]).date()
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


class HistoricalImageProvider(ImageProvider):
    def get(self) -> Tuple[Image.Image, Date]:
        # todo: set up for training
        pass


def crop(image: Image, *, x: int, y: int, width: int, height: int) -> Image:
    return image.crop((x, y, x + width, y + height))