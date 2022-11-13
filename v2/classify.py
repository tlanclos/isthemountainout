import argparse
import tensorflow as tf
import numpy as np

from common.config import model_bucket_name
from common.image import LatestSnapshotImageProvider, SpaceNeedleImageProvider, ImageProvider
from common.frozenmodel import generate_model, labels
from common.storage import GcpBucketStorage
from common.weights import weights
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

    def __init__(self):
        self.model_bucket = GcpBucketStorage(bucket_name=model_bucket_name())

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


def get_image_provider(source: str) -> ImageProvider:
    if source == 'live':
        return SpaceNeedleImageProvider()
    elif source == 'snapshot':
        return LatestSnapshotImageProvider()
    else:
        print(f'Unknown image source {source}')
        raise Exception(f'Unknown image source {source}')


def main(request):
    classifier = Classifier()
    image_provider = get_image_provider(args.source)
    image, date = image_provider.get()

    print(f'Classifying image for date {date}')
    print(classifier.classify(image=image))
    # print(date)
    # image.show()


if __name__ == '__main__':
    main(None)
