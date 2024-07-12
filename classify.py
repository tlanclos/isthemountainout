import os
import argparse
import tensorflow as tf
import numpy as np
import json
import pytz
import sqlite3

from astral import LocationInfo
from astral.sun import sun
from common.image import LatestSnapshotImageProvider, SpaceNeedleImageProvider, ImageProvider, TimestampedSnapshotImageProvider
from common.frozenmodel import generate_model, labels, Label
from common.weights import weights
from common.sheets import ClassificationRow, RangeData
from common.twitter import TwitterApiKeys, TwitterPoster
from datetime import datetime, timedelta
from enum import Enum
from googleapiclient.discovery import build as build_api, Resource
from PIL import Image
from typing import Optional, Tuple, List
from flask import make_response

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


class ImageSource(Enum):
    LIVE = 'live'
    CLOUD_SNAPSHOT = 'cloud-snapshot'
    DISK_SNAPSHOT = 'disk-snapshot'

    def provider(self, *,
                 snapshot_timestamp: Optional[str] = None,
                 disk_snapshot_path: Optional[str] = None) -> ImageProvider:
        if self == ImageSource.LIVE:
            return SpaceNeedleImageProvider()
        elif self in (ImageSource.CLOUD_SNAPSHOT, ImageSource.DISK_SNAPSHOT):
            if snapshot_timestamp is not None:
                return TimestampedSnapshotImageProvider(
                    timestamp=datetime.strptime(
                        snapshot_timestamp, '%Y-%m-%dT%H:%M:%S'),
                    from_disk_path=disk_snapshot_path)
            else:
                return LatestSnapshotImageProvider(from_disk_path=disk_snapshot_path)
        else:
            print(f'Unknown image source {self}')
            raise Exception(f'Unknown image source {self}')


parser = argparse.ArgumentParser(
    description='Classify an image of Mount Rainier')
subparsers = parser.add_subparsers(dest='source')

parser.add_argument(
    '--dry-run',
    action='store_true',
    help='Classify the image and print to the console, but nothing is committed')
parser.add_argument(
    '--local-weights',
    help='Set this flag to the path for the local weights filename, unset will load weights from cloud storage')
parser.add_argument(
    '--local-tracker-db',
    help='Set this flag to the path for the SQLite database that tracks mountain classifications')

live_parser = subparsers.add_parser(
    ImageSource.LIVE.value,
    help='Classify an image directly from the space needle camera')
cloud_snapshot_parser = subparsers.add_parser(
    ImageSource.CLOUD_SNAPSHOT.value,
    help='Classify an image from a snapshot using the cloud image provider')
disk_snapshot_parser = subparsers.add_parser(
    ImageSource.DISK_SNAPSHOT.value,
    help='Classify an image from a snapshot using the disk-based image provider')

cloud_snapshot_parser.add_argument(
    '--snapshot-timestamp',
    help='Set this flag to the snapshot timestamp to use for classification')

disk_snapshot_parser.add_argument(
    '--snapshot-timestamp',
    help='Set this flag to the snapshot timestamp to use for classification')
disk_snapshot_parser.add_argument(
    '--path',
    required=True,
    dest='disk_snapshot_path',
    help='Sets the path for where the snapshots are given')

PACIFIC_TIMEZONE = pytz.timezone('US/Pacific')


class Classifier:
    seattle = LocationInfo(
        name='Seattle',
        region='Washington',
        timezone='America/Los_Angeles',
        latitude=47.6209673,
        longitude=-122.348993
    )
    image_provider: ImageProvider
    local_weights: Optional[str]

    def __init__(self, *, image_provider: ImageProvider, local_weights: Optional[str] = None):
        self.image_provider = image_provider
        self.local_weights = local_weights

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
        image, date = self.image_provider.get()

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


class ClassificationTracker:
    notable_transitions = {
        Label.NIGHT: {Label.HIDDEN, Label.MYSTICAL, Label.BEAUTIFUL},
        Label.HIDDEN: {Label.MYSTICAL, Label.BEAUTIFUL},
        Label.MYSTICAL: {Label.BEAUTIFUL},
        Label.BEAUTIFUL: {Label.HIDDEN},
    }

    def amend(self, classification: ClassificationRow):
        pass

    def read_latest(self, *, count: int) -> List[ClassificationRow]:
        pass

    def should_post(self, classification: Label) -> bool:
        last_classification = self._read_last_notable_classification()
        new_classification_is_notable = classification in ClassificationTracker.notable_transitions[
            last_classification]
        will_classification_settle = self._will_classification_settle_with(
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

    def _will_classification_settle_with(self, classification: Label) -> bool:
        history = [c.classification for c in self.read_latest(count=2)]
        will_it_settle = all(c == classification for c in history)
        next_history = [c.value for c in [*history, classification]]
        if will_it_settle:
            print(
                f'Classification chain {" -> ".join(next_history)} has settled')
        else:
            print(
                f'Classification chain {" -> ".join(next_history)} has not settled')
        return will_it_settle

    def _read_last_notable_classification(self) -> Label:
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
        for row in reversed(self.read_latest(count=100)):
            if row.was_posted or row.classification == Label.NIGHT:
                return row.classification
            elif row.date.date() == yesterday:
                print(
                    f'Post not found since yesterday, assuming {Label.NIGHT}')
                return Label.NIGHT

        # If there has been no posts or night found, just assume that there was
        # night at some point
        return Label.NIGHT


class GoogleSheetsClassificationTracker(ClassificationTracker):
    spreadsheet_id = '1nMkjiqMvsOhj-ljEab2aBvNWy3bJXdot3u2vRXsyI5Q'
    spreadsheet_sheet_name = 'StateV2'
    spreadsheet_range = f'{spreadsheet_sheet_name}!A2:C'
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

    def read_latest(self, *, count: int) -> List[ClassificationRow]:
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


class SqliteClassificationTracker(ClassificationTracker):
    _CLASSIFICATIONS_TABLE_NAME = 'classifications'

    connection: sqlite3.Connection

    def __init__(self, *, path: str) -> None:
        self.connection = sqlite3.connect(path)
        self.__create_database()

    def amend(self, classification: ClassificationRow):
        cursor = self.connection.cursor()
        table_name = SqliteClassificationTracker._CLASSIFICATIONS_TABLE_NAME
        cursor.execute(
            f"INSERT INTO {table_name} (classification_time, classification, was_posted) VALUES (?, ?, ?);",
            (classification.date, classification.classification.value, classification.was_posted))
        cursor.fetchall()
        cursor.close()

    def read_latest(self, *, count: int) -> List[ClassificationRow]:
        cursor = self.connection.cursor()
        table_name = SqliteClassificationTracker._CLASSIFICATIONS_TABLE_NAME
        cursor.execute(
            f"""
            SELECT classification_time, classification, was_posted
            FROM {table_name}
            ORDER BY classification_time DESC
            LIMIT ?
            """, (count,))

        rows: List[ClassificationRow] = []
        for row in cursor.fetchall():
            rows.append(ClassificationRow(
                date=row[0], classification=row[1], was_posted=row[2]))
        cursor.close()
        return rows

    def __create_database(self):
        if self.__table_exists(SqliteClassificationTracker._CLASSIFICATIONS_TABLE_NAME):
            self.__create_classifications_table(
                SqliteClassificationTracker._CLASSIFICATIONS_TABLE_NAME)

    def __table_exists(self, *, table_name: str) -> bool:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
        rows = cursor.rowcount > 0
        cursor.close()
        return rows

    def __create_classifications_table(self, *, table_name: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            f"CREATE TABLE {table_name} (classification_time DATETIME, classification TEXT, was_posted BOOLEAN);")
        cursor.fetchall()
        cursor.close()


def main(request):
    req = request.json
    classifier = Classifier(
        image_provider=ImageSource(req.get('source')).provider(
            snapshot_timestamp=req.get('snapshot_timestamp', None),
            disk_snapshot_path=req.get('disk_snapshot_path', None))
        local_weights=req.get('local_weights', None))
    classification, image = classifier.classify_next()
    print('Classification', classification)

    local_tracker_db = req.get('local_tracker_db', None)
    classification_tracker = SqliteClassificationTracker(
        path=local_tracker_db) if local_tracker_db else GoogleSheetsClassificationTracker()

    if classification_tracker.should_post(classification.classification):
        classification.was_posted = True
        print(f'Posting {classification}')
        if not args.dry_run:
            classification_tracker.amend(classification)
            twitter = TwitterPoster(keys=TwitterApiKeys.from_storage())
            twitter.post(
                status=twitter.status_for_label(classification.classification),
                image=twitter.brand_image(image),
                tags=twitter.tags_for_label(classification.classification))
    else:
        print(f'Classification did not change from {classification}')
        if not args.dry_run:
            classification_tracker.amend(classification)

    return make_response((json.dumps({
        'date': classification.date.isoformat(),
        'classification': classification.classification.name,
    }), 200, {'Content-Type': 'application/json'}))


if __name__ == '__main__':
    args = parser.parse_args()

    class FakeRequest:
        @property
        def json(self):
            return {
                'source': args.source,
                'snapshot_timestamp': args.snapshot_timestamp,
                'local_weights': args.local_weights,
                'local_tracker_db': args.local_tracker_db,
                'disk_snapshot_path': args.disk_snapshot_path,
                'dry_run': args.dry_run,
            }
    main(FakeRequest())
