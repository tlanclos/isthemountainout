import requests
import shutil
import io
from PIL import Image

def download_image(url: str) -> Image:
    request = requests.get(url, stream=True)
    if request.status_code == 200:
        request.raw.decode_content = True
        data = io.BytesIO()
        shutil.copyfileobj(request.raw, data)
        data.seek(0)
        return Image.open(data)
    else:
        raise IOError('Could not download latest image')
