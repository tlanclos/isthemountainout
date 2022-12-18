import os
import argparse
import tensorflow as tf
import numpy as np
import json
import pytz

from astral import LocationInfo
from astral.sun import sun
from common.config import model_bucket_name
from common.image import LatestSnapshotImageProvider, SpaceNeedleImageProvider, ImageProvider, TimestampedSnapshotImageProvider
from common.frozenmodel import generate_model, labels, Label
from common.storage import GcpBucketStorage
from common.weights import weights
from common.sheets import ClassificationRow, RangeData
from common.twitter import TwitterApiKeys, TwitterPoster
from datetime import datetime, timedelta
from googleapiclient.discovery import build as build_api, Resource
from PIL import Image
from typing import Optional, Tuple, List
from flask import make_response

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

parser = argparse.ArgumentParser(
    description='Classify an image of Mount Rainier')
parser.add_argument('source', choices=[
                    'live', 'snapshot'], help='Source image provider')
parser.add_argument(
    '--local-weights', help='Set this flag to the path for the local weights filename, unset will load weights from cloud storage')
parser.add_argument('--snapshot-timestamp',
                    help='Set this flag to the snapshot timestamp to use for classification')

PACIFIC_TIMEZONE = pytz.timezone('US/Pacific')


class Classifier:
    seattle = LocationInfo(
        name='Seattle',
        region='Washington',
        timezone='America/Los_Angeles',
        latitude=47.6209673,
        longitude=-122.348993
    )
    model_bucket: GcpBucketStorage
    image_source: str
    local_weights: Optional[str]
    snapshot_timestamp: Optional[str]

    def __init__(self, *, image_source: str, local_weights: Optional[str] = None, snapshot_timestamp: Optional[str] = None):
        self.model_bucket = GcpBucketStorage(bucket_name=model_bucket_name())
        self.image_source = image_source
        self.local_weights = local_weights
        self.snapshot_timestamp = snapshot_timestamp

    def _load_model(self):
        with weights(local_filename=self.local_weights) as filepath:
            return generate_model(weights_filepath=filepath)

    def classify(self, *, image: Image.Image):
        model = self._load_model()
        img_array = tf.keras.utils.img_to_array(
            image).astype('float32')
        img_array = tf.expand_dims(img_array, 0)
        score = tf.nn.softmax(model.predict(img_array))
        return labels()[np.argmax(score, axis=1)[0]]

    def classify_next(self) -> Tuple[ClassificationRow, Image.Image]:
        image_provider = self._get_image_provider(self.image_source)
        image, date = image_provider.get()

        print(f'Classifying image for date {date}')
        classification = self.classify(image=image)

        if self.__is_night(date) and classification != Label.NIGHT:
            print(
                f'Faulty classification detected, defaulting to {Label.NIGHT}: was {classification}, but is actually night time')
            classification = Label.NIGHT
        elif not self.__is_night(date) and classification == Label.NIGHT:
            print(
                f'Faulty classification detected, defaulting to {Label.HIDDEN}: was {classification}, but is not night time')
            classification = Label.HIDDEN

        return ClassificationRow(
            date=date,
            classification=classification), image

    def __is_night(self, timestamp: datetime) -> bool:
        date = timestamp.replace(tzinfo=PACIFIC_TIMEZONE)
        info = sun(Classifier.seattle.observer, date=datetime(
            year=date.year, month=date.month, day=date.day, tzinfo=PACIFIC_TIMEZONE))
        return date < info['dawn'] or date > info['dusk']

    def _get_image_provider(self, source: str) -> ImageProvider:
        if source == 'live':
            return SpaceNeedleImageProvider()
        elif source == 'snapshot':
            if self.snapshot_timestamp is not None:
                return TimestampedSnapshotImageProvider(
                    timestamp=datetime.strptime(self.snapshot_timestamp, '%Y-%m-%dT%H:%M:%S'))
            else:
                return LatestSnapshotImageProvider()
        else:
            print(f'Unknown image source {source}')
            raise Exception(f'Unknown image source {source}')


class ClassificationTracker:
    spreadsheet_id = '1nMkjiqMvsOhj-ljEab2aBvNWy3bJXdot3u2vRXsyI5Q'
    spreadsheet_sheet_name = 'StateV2'
    spreadsheet_range = f'{spreadsheet_sheet_name}!A2:C'
    notable_transitions = {
        Label.NIGHT: {Label.HIDDEN, Label.MYSTICAL, Label.BEAUTIFUL},
        Label.HIDDEN: {Label.MYSTICAL, Label.BEAUTIFUL},
        Label.MYSTICAL: {Label.BEAUTIFUL},
        Label.BEAUTIFUL: {Label.HIDDEN},
    }
    service: Resource

    def __init__(self) -> None:
        self.service = build_api('sheets', 'v4')

    def amend(self, classification: ClassificationRow):
        spreadsheet_data = self.service.spreadsheets() \
            .get(spreadsheetId=ClassificationTracker.spreadsheet_id) \
            .execute()
        state_sheet = list(filter(
            lambda sheet: sheet['properties']['title'] ==
            ClassificationTracker.spreadsheet_sheet_name, spreadsheet_data['sheets']))[0]
        state_sheet_id = state_sheet['properties']['sheetId']
        self.service.spreadsheets().values().append(
            spreadsheetId=ClassificationTracker.spreadsheet_id,
            range=ClassificationTracker.spreadsheet_range,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': [classification.as_list()]},
        ).execute()
        last_classification_range = self.__get_latest_classification_range()
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=ClassificationTracker.spreadsheet_id,
            body={
                'requests': [{
                    'copyPaste': {
                        'source': {
                            'sheetId': state_sheet_id,
                            'startColumnIndex': 3,
                            'endColumnIndex': 4,
                            'startRowIndex': 1,
                            'endRowIndex': 2,
                        },
                        'destination': {
                            'sheetId': state_sheet_id,
                            'startColumnIndex': 3,
                            'endColumnIndex': 4,
                            # Index for row starts at 1, so subtract an additional row to
                            # get the proper starting location
                            'startRowIndex': last_classification_range.start_cell.row - 2,
                            'endRowIndex': last_classification_range.start_cell.row - 1,
                        },
                        'pasteType': 'PASTE_FORMULA',
                        'pasteOrientation': 'NORMAL',
                    },
                }],
            }
        ).execute()

    def should_post(self, classification: Label) -> bool:
        last_classification = self.read_last_notable_classification()
        new_classification_is_notable = classification in ClassificationTracker.notable_transitions[
            last_classification]
        will_classification_settle = self.will_classification_settle_with(
            classification)
        if not new_classification_is_notable and not will_classification_settle:
            print(
                f'Classification will not post because {classification} is not notable from {last_classification} and will not settle')
            return False
        elif not new_classification_is_notable:
            print(
                f'Classification will not post because {classification} is not notable from {last_classification}')
            return False
        elif not will_classification_settle:
            print(
                f'Classification will not post because it will not settle with the new classification, {classification}')
            return False
        else:
            print(
                f'Classification will post because {classification} is notable from {last_classification} and will settle with the new classification')
            return True

    def will_classification_settle_with(self, classification: Label) -> bool:
        history = [
            c.classification for c in self.__read_latest_classifications(count=2)]
        will_it_settle = all(c == classification for c in history)
        next_history = [c.value for c in [*history, classification]]
        if will_it_settle:
            print(
                f'Classification chain {" -> ".join(next_history)} has settled')
        else:
            print(
                f'Classification chain {" -> ".join(next_history)} has not settled')
        return will_it_settle

    def read_last_notable_classification(self) -> Label:
        """
        Find which classification in the classification history is considered "notable".
        That means that the classification happened on the same day and was posted. Classifications
        that happen at night are considered the reset zone so mountain classifications will always
        be posted the next day.
        """
        yesterday = datetime.now(PACIFIC_TIMEZONE).date() - \
            timedelta(days=1)

        # Search back 100 (around 2 days) rows to see when the last posted
        # classification was and take that as the last classification.
        for row in reversed(self.__read_latest_classifications(count=100)):
            if row.was_posted or row.classification == Label.NIGHT:
                return row.classification
            elif row.date.date() == yesterday:
                print(
                    f'Post not found since yesterday, assuming {Label.NIGHT}')
                return Label.NIGHT

        # If there has been no posts or night found, just assume that there was
        # night at some point
        return Label.NIGHT

    def __read_latest_classifications(self, *, count: int) -> List[ClassificationRow]:
        range = self.__get_latest_classification_range()
        response = self.service.spreadsheets().values().get(
            spreadsheetId=ClassificationTracker.spreadsheet_id,
            range=str(RangeData.of(
                sheet_name=range.sheet_name,
                start=range.start_cell.minus_rows(count, min_row=2),
                end=range.end_cell,
            ))
        ).execute()
        return [
            ClassificationRow(
                date=datetime.strptime(
                    value[0], r'%Y-%m-%dT%H:%M:%S').replace(tzinfo=PACIFIC_TIMEZONE),
                classification=Label(value[1]),
                was_posted=True if value[2] == 'TRUE' else False,
            ) for value in response.get('values', [])]

    def __get_latest_classification_range(self) -> RangeData:
        response = self.service.spreadsheets().values().append(
            spreadsheetId=ClassificationTracker.spreadsheet_id,
            range=ClassificationTracker.spreadsheet_range,
            valueInputOption='USER_ENTERED',
            body={'values': [['', '', '']]}
        ).execute()
        return RangeData(response.get('updates', {}).get('updatedRange', ''))


def main(request):
    req = request.json
    classifier = Classifier(
        image_source=req.get('source', 'snapshot'),
        local_weights=req.get('local_weights', None),
        snapshot_timestamp=req.get('snapshot_timestamp', None))
    classification, image = classifier.classify_next()
    print('Classification', classification)
    classification_tracker = ClassificationTracker()

    if classification_tracker.should_post(classification.classification):
        classification.was_posted = True
        classification_tracker.amend(classification)
        twitter = TwitterPoster(keys=TwitterApiKeys.from_storage())
        twitter.post(
            status=twitter.status_for_label(classification),
            image=twitter.brand_image(image),
            tags=twitter.tags_for_label(classification))
    else:
        classification_tracker.amend(classification)

    return make_response((json.dumps({
        'date': classification.date.isoformat(),
        'classification': classification.classification.name,
    }), 200, {'Content-Type': 'application/json'}))


if __name__ == '__main__':
    args = parser.parse_args()

    class FakeRequest:
        @ property
        def json(self):
            return {
                'source': args.source,
                'local_weights': args.local_weights,
                'snapshot_timestamp': args.snapshot_timestamp,
            }
    main(FakeRequest())
