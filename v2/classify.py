import os
import tempfile
import tensorflow as tf
from common.config import model_bucket_name, model_filename
from common.image import LatestSnapshotImageProvider, SpaceNeedleImageProvider, ImageProvider
from common.frozenmodel import generate_model
from common.storage import GcpBucketStorage
from PIL import Image
import argparse


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
        if args.local_weights:
            print(f'Loading weight locally from {args.local_weights}')
            return generate_model(weights_filepath=args.local_weights)
        else:
            print(f'Loading weights from the cloud')
            try:
                blob = self.model_bucket.get(model_filename())
                f = tempfile.TemporaryFile(delete=False)
                f.write(blob.download_as_bytes())
                model = generate_model(weights_filepath=f.name)
            finally:
                f.close()
                os.unlink(f.name)
                return model

    def classify(self, *, image: Image.Image):
        model = self._load_model()
        img_array = tf.keras.utils.img_to_array(image) / 255.0
        # img_array = img_array.astype('float32')
        img_array = tf.expand_dims(img_array, 0)
        score = tf.nn.softmax(model.predict(img_array))
        print(score)


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
    classifier.classify(image=image)
    # print(date)
    # image.show()


if __name__ == '__main__':
    main(None)
