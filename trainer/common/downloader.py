import requests
import shutil
import io
from urllib.parse import urlparse
from datetime import datetime, date as Date
from PIL import Image
from typing import Tuple

def download_image(url: str) -> Tuple[Image.Image, Date]:
    redirected_url = requests.head(url, allow_redirects=True).url
    # Example format: https://storage.roundshot.com/544a1a9d451563.40343637/2021-07-02/14-40-00/2021-07-02-14-40-00_original.jpg
    date = datetime.fromisoformat(list(filter(None, urlparse(redirected_url).path.split('/')))[1]).date()
    req = requests.get(redirected_url, stream=True)
    if req.status_code == 200:
        req.raw.decode_content = True
        data = io.BytesIO()
        shutil.copyfileobj(req.raw, data)
        data.seek(0)
        image = Image.open(data)
        width, height = image.size
        scale = height / 2048  # The original image size had a height of 2048, so try to keep it within those bounds keeping the aspect ratio
        return image.resize((int(width / scale), int(height / scale))), date
    else:
        raise IOError(f'Could not download latest image from {url} -> {redirected_url}', req)
