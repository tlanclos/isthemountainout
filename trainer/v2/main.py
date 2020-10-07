import json
import io
import os

import common.model as m
import tensorflow as tf

from common import twitter, downloader
from common.classifier import Classifier
from common.image import preprocess, brand
from enum import Enum
from google.cloud import storage
from PIL import Image
from typing import List, Optional

LAST_CLASSIFICATION_STATE_FILE = 'is-the-mountain-out-state.txt'
LAST_IMAGE_STATE_FILE = 'is-the-mountain-out-image.png'

class Label(Enum):
    NIGHT = 'Night'
    NOT_VISIBLE = 'NotVisible'
    MYSTICAL = 'Mystical'
    BEAUTIFUL = 'Beautiful'

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
    classifier = Classifier(model=__gen_model(len(labels)), labels=labels)

    # download the image, preprocess it, and get its classification/confidence
    image = downloader.download_image('http://backend.roundshot.com/cams/241/original')
    classification, confidence = classifier.classify(preprocess(image))
    classification = Label(classification)

    # deterimine if there is a change in states
    data = request.get_json(force=True)
    last_classification = Label(__get_last_classification(bucket=data['bucket']))

    if classification in notable_transitions[last_classification]:
        # calculate the branded image
        branded = brand(image, brand=__load_brand())

        # update the last successful image detection and status
        __update_last_image(bucket=data['bucket'], image=branded)
        __update_last_classification(bucket=data['bucket'], classification=classification)

        # post image to twitter
        print('Posting image to twitter!')
        twitter.tweet(
            keys=__load_twitter_keys(bucket=data['bucket']),
            tweet_status=twitter.message_for(classification),
            image=branded)
    elif classification == Label.NIGHT:
        # ensure that the status gets reset at night
        __update_last_classification(bucket=data['bucket'], classification=classification)

    return f'{classification} {confidence:.2f}%'


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


def __get_last_classification(*, bucket: str) -> Optional[str]:
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.get_blob(LAST_CLASSIFICATION_STATE_FILE)
    if not blob:
        return None
    else:
        return blob.download_as_string().decode('utf-8').strip()


def __update_last_classification(*, bucket: str, classification: str) -> None:
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.get_blob(LAST_CLASSIFICATION_STATE_FILE)
    if blob is None:
        blob = storage.blob.Blob(LAST_CLASSIFICATION_STATE_FILE, bucket)
    blob.upload_from_string(classification)


def __update_last_image(*, bucket: str, image: Image) -> None:
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.get_blob(LAST_IMAGE_STATE_FILE)
    if blob is None:
        blob = storage.blob.Blob(LAST_IMAGE_STATE_FILE, bucket)

    with io.BytesIO() as output:
        image.save(output, format="PNG")
        blob.upload_from_string(output.getvalue())


def __gen_model(classes: int) -> tf.keras.Model:
    shape = (224, 224, 3)
    inputs = tf.keras.Input(shape=shape)
    outputs = m.chained(
    tf.keras.layers.add([
        m.chained(
            inputs,
            tf.keras.layers.Lambda(
                lambda image: tf.image.rgb_to_grayscale(image)),
            tf.keras.layers.Conv2D(
                filters=64, kernel_size=3, activation='relu'),
            tf.keras.layers.MaxPooling2D(2),
            tf.keras.layers.Conv2D(
                filters=64, kernel_size=3, activation='relu'),
            tf.keras.layers.MaxPooling2D(2),
            tf.keras.layers.Dropout(0.1),
            tf.keras.layers.Conv2D(
                filters=64, kernel_size=3, activation='relu'),
            tf.keras.layers.MaxPooling2D(2),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32),
        ),
        m.chained(
            inputs,
            tf.keras.layers.Lambda(
                lambda image: tf.image.rgb_to_grayscale(image)),
            tf.keras.layers.Conv2DTranspose(
                filters=64, kernel_size=3, activation='relu'),
            tf.keras.layers.MaxPooling2D(2),
            tf.keras.layers.Conv2DTranspose(
                filters=64, kernel_size=3, activation='relu'),
            tf.keras.layers.MaxPooling2D(2),
            tf.keras.layers.Dropout(0.1),
            tf.keras.layers.Conv2DTranspose(
                filters=64, kernel_size=3, activation='relu'),
            tf.keras.layers.MaxPooling2D(2),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32),
        ),
    ]),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(classes),
    tf.keras.layers.Activation('softmax'))
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.build(input_shape=(None, *shape))
    model.load_weights('isthemountainout.h5')
    return model

if __name__ == '__main__':
    class TestRequest:
        def get_json(self, **kwargs):
            return {'bucket': 'isthemountainout.appspot.com'}

    print(classify(TestRequest()))