import os
import tempfile
import tensorflow as tf
from common.config import model_bucket_name, model_filename
from common.image import LatestSnapshotImageProvider
from common.frozenmodel import generate_model
from common.storage import GcpBucketStorage
from PIL import Image


class Classifier:
    model_bucket: GcpBucketStorage

    def __init__(self):
        self.model_bucket = GcpBucketStorage(bucket_name=model_bucket_name())

    def _load_model(self):
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


def main(request):
    classifier = Classifier()
    image_provider = LatestSnapshotImageProvider()
    image, date = image_provider.get()
    classifier.classify(image=image)
    # print(date)
    # image.show()


if __name__ == '__main__':
    main(None)
