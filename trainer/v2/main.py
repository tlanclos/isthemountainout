import json
import os

import tensorflow as tf

from astral import LocationInfo
from astral.sun import sun
from common import twitter, downloader, frozenmodel
from common.classifier import Classifier
from common.image import preprocess, brand
from googleapiclient.discovery import build
from datetime import datetime, timezone
from enum import Enum
from google.cloud import storage
from PIL import Image
from typing import List

LAST_CLASSIFICATION_STATE_FILE = 'is-the-mountain-out-state.txt'
LAST_IMAGE_STATE_FILE = 'is-the-mountain-out-image.png'
SPREADSHEET_ID = '1nMkjiqMvsOhj-ljEab2aBvNWy3bJXdot3u2vRXsyI5Q'


class Label(Enum):
    NIGHT = 'Night'
    NOT_VISIBLE = 'NotVisible'
    MYSTICAL = 'Mystical'
    BEAUTIFUL = 'Beautiful'


seattle = LocationInfo(
    name='Seattle',
    region='Washington',
    timezone='America/Los_Angeles',
    latitude=47.6209673,
    longitude=-122.348993
)
notable_transitions = {
    Label.NIGHT: {Label.NOT_VISIBLE, Label.MYSTICAL, Label.BEAUTIFUL},
    Label.NOT_VISIBLE: {Label.MYSTICAL, Label.BEAUTIFUL},
    Label.MYSTICAL: {Label.BEAUTIFUL},
    Label.BEAUTIFUL: {Label.NOT_VISIBLE}
}


def classify(request) -> str:
    # initialize labels, model, and classifier
    __setup_gpu()
    labels = __load_labels()
    classifier = Classifier(
        model=frozenmodel.generate(len(labels)), labels=labels)

    # download the image, preprocess it, and get its classification/confidence
    image = downloader.download_image(
        'http://backend.roundshot.com/cams/241/original')
    classification, confidence = classifier.classify(preprocess(image))
    classification = Label(classification)

    now = datetime.now(timezone.utc)
    if classification == Label.NIGHT and not __is_night(now):
        nowstr = now.strftime('%B %d %Y %H:%M:%S %Z')
        print(
            f'[WARN] Faulty classification detected [{classification}] @ [{nowstr}]')
        return f'{classification} {confidence:.2f}%'

    # deterimine if there is a change in states
    data = request.get_json(force=True)
    last_classification = __get_last_classification()
    print(f'[INFO] Last classification was {last_classification.value}')
    __update_last_classification(classification=classification)

    if classification in notable_transitions[last_classification]:
        # calculate the branded image
        branded = brand(image, brand=__load_brand())

        # update the last successful status
        __update_last_classification(classification=classification)

        # post image to twitter
        print('[INFO] Posting image to twitter!')
        twitter.tweet(
            keys=__load_twitter_keys(bucket=data['bucket']),
            tweet_status=twitter.message_for(classification),
            image=branded)
    elif classification == Label.NIGHT:
        # ensure that the status gets reset at night
        __update_last_classification(classification=classification)

    print(
        f'[INFO] classification={classification} confidence={confidence:.2f}%')
    return f'{classification} {confidence:.2f}%'


def __is_night(date: datetime) -> bool:
    info = sun(seattle.observer, date=datetime(
        year=date.year, month=date.month, day=date.day))
    return date < info['dawn'] or date > info['dusk']


def __setup_gpu() -> None:
    for device in tf.config.experimental.list_physical_devices('GPU'):
        tf.config.experimental.set_memory_growth(device, True)


def __load_labels() -> List[str]:
    with open('savelabels.txt', 'r') as f:
        return sorted([label.strip() for label in f.readlines()])


def __load_brand() -> Image:
    return Image.open(os.path.join('branding', 'branding_1920x1080.png'))


def __load_twitter_keys(*, bucket: str) -> twitter.ApiKeys:
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.get_blob('is-the-mountain-out-keys.json')
    keys = json.loads(blob.download_as_string().decode('utf-8'))
    return twitter.ApiKeys(
        consumer_key=keys['consumer_key'],
        consumer_key_secret=keys['consumer_key_secret'],
        access_token=keys['access_token'],
        access_token_secret=keys['access_token_secret'],
    )


def __get_last_classification() -> Label:
    service = build('sheets', 'v4')
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='A1').execute()
    values = result.get('values', [])
    return Label(values[0][0])


def __update_last_classification(*, classification: Label) -> None:
    print(f'[INFO] Updating classification={classification.value}')
    service = build('sheets', 'v4')
    values = service.spreadsheets().values()
    values.update(spreadsheetId=SPREADSHEET_ID, range='A1', valueInputOption='RAW', body={
        'values': [[classification.value]]
    }).execute()


if __name__ == '__main__':
    class TestRequest:
        def get_json(self, **kwargs):
            return {'bucket': 'isthemountainout.appspot.com'}

    print(classify(TestRequest()))
