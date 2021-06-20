import json
import os
import hashlib

import tensorflow as tf

from astral import LocationInfo
from astral.sun import sun
from common import twitter, downloader, frozenmodel
from common.classifier import Classifier
from common.frozenmodel import Label
from common.image import preprocess, brand
from common.sheets import RangeData, ClassificationRow
from googleapiclient.discovery import build
from datetime import datetime, timezone
from google.cloud import storage
from io import BytesIO
from PIL import Image
from typing import List, Optional

LAST_CLASSIFICATION_STATE_FILE = 'is-the-mountain-out-state.txt'
LAST_IMAGE_STATE_FILE = 'is-the-mountain-out-image.png'
SPREADSHEET_ID = '1nMkjiqMvsOhj-ljEab2aBvNWy3bJXdot3u2vRXsyI5Q'


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
    # get now
    now = datetime.now(timezone.utc)
    
    # extract the request data
    data = request.get_json(force=True)

    # initialize labels, model, and classifier
    __setup_gpu()
    labels = frozenmodel.labels()
    weights_filepath = __load_weights(bucket=data['bucket'])
    classifier = Classifier(model=frozenmodel.generate(weights_filepath=weights_filepath), labels=labels)

    # download the image, preprocess it, and get its classification/confidence
    image = downloader.download_image(
        'https://backend.roundshot.com/cams/241/original')
    classification, confidence = classifier.classify(preprocess(image))

    # save a cropped image for historical lookup/retraining
    __store_image(
        brand(image, brand=__load_brand()),
        name=now.strftime(f'mtrainier-%Y%m%dT%H%M%S'),
        bucket=data['bucket'])
    
    # detect fault classifications between day and night
    if (classification == Label.NIGHT and not __is_night(now)) or (classification != Label.NIGHT and __is_night(now)):
        nowstr = now.strftime('%B %d %Y %H:%M:%S %Z')
        print(
            f'[WARN] Faulty classification detected [{classification.value}] @ [{nowstr}]')
        return f'{classification} {confidence:.2f}%'

    # deterimine if there is a change in states
    last_classification = __get_last_classification()
    if last_classification is None:
        print(f'[WARN] Cannot determine the last classification, to fix please mark some image as posted')
        return f'{classification} {confidence:.2f}%'

    print(f'[INFO] Last classification was {last_classification.value}')
    if classification in notable_transitions[last_classification] and __has_classification_settled(classification):
        # calculate the branded image
        branded = brand(image, brand=__load_brand())

        # update the last successful status
        __update_last_classification(ClassificationRow(
            classification=classification,
            date=now,
            was_posted=True,
        ))

        # post image to twitter
        print('[INFO] Posting image to twitter!')
        twitter.tweet(
            keys=__load_twitter_keys(bucket=data['bucket']),
            tweet_status=twitter.message_for(classification),
            tags=twitter.tags(classification),
            image=branded)
    elif classification == Label.NIGHT and last_classification != Label.NIGHT:
        # ensure that the status gets reset at night
        __update_last_classification(ClassificationRow(
            classification=classification,
            date=now,
            was_posted=False,
        ))

    print(
        f'[INFO] classification={classification.value} confidence={confidence:.2f}%')
    return f'{classification.value} {confidence:.2f}%'


def __is_night(date: datetime) -> bool:
    # TODO(tlanclos): This needs to be fixed. For context, see classification info sample below. This was rendered on 6/19/2021 @ 5:21 PM PT
    # [INFO] is_night=True [now]=2021-06-20 00:21:38.702407+00:00 [dawn]=2021-06-20 11:30:10.746244+00:00 [dusk]=2021-06-21 04:52:03.242519+00:00
    info = sun(seattle.observer, date=datetime(
        year=date.year, month=date.month, day=date.day))
    is_night = date < info['dawn'] or date > info['dusk']
    print(f"[INFO] is_night={is_night} [now]={date} [dawn]={info['dawn']} [dusk]={info['dusk']}")
    return is_night


def __setup_gpu() -> None:
    for device in tf.config.experimental.list_physical_devices('GPU'):
        tf.config.experimental.set_memory_growth(device, True)


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


def __load_weights(*, bucket: str, filepath: str = '/tmp/isthemountainout.h5') -> str:
    if os.path.exists(filepath):
        print(f'{filepath} already existed, returning early')
        return filepath
    else:
        print(f'{filepath} does not exist, downloading weights')
        client = storage.Client()
        bucket = client.get_bucket(bucket)
        blob = bucket.get_blob('isthemountainout.h5')
        with open(filepath, 'wb') as f:
            blob.download_to_file(f)
        return filepath


def __has_classification_settled(classification: Label) -> bool:
    prev_classifications = __get_prev_classifications(count=2)
    print(f'[INFO] Checking for settled classification={classification.value} in: {",".join([c.classification.value for c in prev_classifications])}')
    return all(c.classification == classification for c in prev_classifications)


def __get_last_classification() -> Optional[Label]:
    # Search back 100 (around 2 days) rows to see when the last posted 
    # classification was and take that as the last classification.
    for row in reversed(__get_prev_classifications(count=100)):
        if row.was_posted:
            return row.classification
    return None


def __get_prev_classifications(*, count: int) -> List[ClassificationRow]:
    lastRowRange = __get_latest_classification_range()
    service = build('sheets', 'v4')
    result = service.spreadsheets().values() \
        .get(
            spreadsheetId=SPREADSHEET_ID,
            range=str(RangeData.of(
                sheetName=lastRowRange.sheetName,
                start=lastRowRange.startCell.minusRows(count, min_row=2),
                end=lastRowRange.endCell,
            )),
        ).execute()
    return [
        ClassificationRow(
            date=datetime.fromisoformat(value[0]),
            classification=Label(value[1]),
            was_posted=True if value[2] else False,
        ) for value in result.get('values', [])
    ]


def __get_latest_classification_range() -> RangeData:
    service = build('sheets', 'v4')
    return RangeData(service.spreadsheets().values() \
        .append(
            spreadsheetId=SPREADSHEET_ID,
            range='State!A2:C',
            valueInputOption='USER_ENTERED',
            body={'values': [['', '', '']]}
        ) \
        .execute() \
        .get('updates', {}) \
        .get('updatedRange', ''))


def __update_last_classification(classification: ClassificationRow) -> None:
    print(f'[INFO] Updating classification={classification.value}')
    service = build('sheets', 'v4')
    service.spreadsheets().values() \
        .append(
            spreadsheetId=SPREADSHEET_ID,
            range='State!A2:C',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': [classification.asList()]},
        ).execute()

def __store_image(image: Image.Image, *, name: str, bucket: str) -> None:
    print(f'[INFO] Storing image name={name}')
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.blob(f'mt-rainier-history/{name}.png')
    imagefile = BytesIO()
    image.save(imagefile, format='PNG')
    blob.upload_from_string(imagefile.getvalue())

if __name__ == '__main__':
    class TestRequest:
        def get_json(self, **kwargs):
            return {'bucket': 'isthemountainout.appspot.com'}

    print(classify(TestRequest()))
