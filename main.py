import requests
import shutil
import os
from PIL import Image
from google.cloud import storage
from typing import Optional
from trainer.classifier import Classifier, ClassifierOptions
from trainer.common.path import get_script_path

classifier = None
branding = None
STATE_FILE = '/is-the-mountain-out-state.txt'


def classify(request):
    global classifier
    if classifier is None:
        classifier = Classifier(
            ClassifierOptions(
                saved_model_path=os.path.join(
                    'trainer', 'isthemountainout.h5'),
                save_labels_file=os.path.join(
                    'trainer', 'savelabels.txt'),
            )
        )

    classification, confidence, image = classifier.classify(__download_image(
        "http://backend.roundshot.com/cams/241/original"))
    branded_image = __brand_image(image)

    data = request.get_json(force=True)
    state = __get_last_classification(data['bucket'])
    if state != classification:
        posted_image = True
        __update_last_classification(data['bucket'])
    else:
        posted_image = False

    return f'{classification} {confidence:.2f}% {posted_image}'


def __download_image(url: str, *, to_file: str = '/tmp/current.jpg') -> str:
    # download an image and place it in a temporary file
    request = requests.get(url, stream=True)
    if request.status_code == 200:
        request.raw.decode_content = True
        with open(to_file, 'wb') as f:
            shutil.copyfileobj(request.raw, f)

        return to_file
    else:
        raise IOError('Could not download latest image')


def __brand_image(image: Image.Image) -> Image.Image:
    global branding
    if branding is None:
        branding = Image.open(os.path.join(
            get_script_path(), '..', 'branding', 'branding_1920x1080.png'))

    image = image.crop((7036, 162, 8956, 1242))
    image.paste(branding, (0, 0), branding)
    return image


def __get_last_classification(bucket: str) -> Optional[str]:
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.get_blob(STATE_FILE)
    if not blob:
        return None
    else:
        return blob.download_as_string().decode('utf-8')


def __update_last_classification(bucket: str, *, state: str) -> None:
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.get_blob(STATE_FILE)
    blob.update_from_string(state)
