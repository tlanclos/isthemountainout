import argparse
import tensorflow as tf
import numpy as np

from common.config import model_bucket_name
from common.image import LatestSnapshotImageProvider, SpaceNeedleImageProvider, ImageProvider
from common.frozenmodel import generate_model, labels
from common.storage import GcpBucketStorage
from common.weights import weights
from common.sheets import ClassificationRow
from googleapiclient.discovery import build as build_api
from PIL import Image


parser = argparse.ArgumentParser(
    description='Classify an image of Mount Rainier')
parser.add_argument('source', choices=[
                    'live', 'snapshot'], help='Source image provider')
parser.add_argument(
    '--local-weights', help='Set this flag to the path for the local weights filename, unset will load weights from cloud storage')
args = parser.parse_args()


class Classifier:
    model_bucket: GcpBucketStorage
    image_source: str

    def __init__(self, *, image_source: str):
        self.model_bucket = GcpBucketStorage(bucket_name=model_bucket_name())
        self.image_source = image_source

    def _load_model(self):
        with weights(local_filename=args.local_weights) as filepath:
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
    classifier = Classifier(image_source=args.source)
    classification_tracker = ClassificationTracker()
    classification_tracker.amend(classifier.classify_next())


if __name__ == '__main__':
    main(None)
