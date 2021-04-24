import requests
import shutil
import io
from PIL import Image

def download_image(url: str) -> Image:
    redirected_url = requests.head(url, allow_redirects=True).url
    req = requests.get(redirected_url, stream=True)
    if req.status_code == 200:
        req.raw.decode_content = True
        data = io.BytesIO()
        shutil.copyfileobj(req.raw, data)
        data.seek(0)
        return Image.open(data)
    else:
        raise IOError(f'Could not download latest image from {url} -> {redirected_url}', req)
