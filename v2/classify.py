import argparse
import tensorflow as tf
import numpy as np
import json

from common.config import model_bucket_name
from common.image import LatestSnapshotImageProvider, SpaceNeedleImageProvider, ImageProvider, TimestampedSnapshotImageProvider
from common.frozenmodel import generate_model, labels
from common.storage import GcpBucketStorage
from common.weights import weights
from common.sheets import ClassificationRow
from datetime import datetime
from googleapiclient.discovery import build as build_api
from PIL import Image
from typing import Optional
from flask import make_response


parser = argparse.ArgumentParser(
    description='Classify an image of Mount Rainier')
parser.add_argument('source', choices=[
                    'live', 'snapshot'], help='Source image provider')
parser.add_argument(
    '--local-weights', help='Set this flag to the path for the local weights filename, unset will load weights from cloud storage')
parser.add_argument('--snapshot-timestamp',
                    help='Set this flag to the snapshot timestamp to use for classification')


class Classifier:
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
        img_array = tf.keras.utils.img_to_array(image) / 255.0
        # img_array = img_array.astype('float32')
        img_array = tf.expand_dims(img_array, 0)
        score = tf.nn.softmax(model.predict(img_array))
        return labels()[np.argmax(score)]

    def classify_next(self) -> ClassificationRow:
        image_provider = self._get_image_provider(self.image_source)
        image, date = image_provider.get()

        print(f'Classifying image for date {date}')
        return ClassificationRow(
            date=date,
            classification=self.classify(image=image))

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
    def __init__(self) -> None:
        pass

    def amend(self, classification: ClassificationRow):
        service = build_api('sheets', 'v4')
        service.spreadsheets().values().append(
            spreadsheetId='1nMkjiqMvsOhj-ljEab2aBvNWy3bJXdot3u2vRXsyI5Q',
            range='StateV2!A2:C',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': [[*classification.as_list(), 'FALSE']]},
        ).execute()


def main(request):
    req = request.json
    classifier = Classifier(
        image_source=req.get('source', 'snapshot'),
        local_weights=req.get('local_weights', None),
        snapshot_timestamp=req.get('snapshot_timestamp', None))
    classification = classifier.classify_next()
    print(classification)
    classification_tracker = ClassificationTracker()
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
                'local_weights': args.local_weights,
                'snapshot_timestamp': args.snapshot_timestamp,
            }
    main(FakeRequest())
