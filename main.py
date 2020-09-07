import requests
import shutil
import os
import io
import json
import tweepy
from PIL import Image
from google.cloud import storage
from typing import Optional
from trainer.classifier import Classifier, ClassifierOptions
from trainer.common.path import get_script_path

classifier = None
branding = None
twitter_keys = None

STATE_FILE = 'is-the-mountain-out-state.txt'
IMAGE_FILE = 'is-the-mountain-out-image.png'
TWITTER_KEYS_FILE = 'is-the-mountain-out-keys.json'

TEMP_DOWNLOAD_IMAGE = '/tmp/current.jpg'
TEMP_TWITTER_IMAGE_POST = '/tmp/image-to-tweet.png'


def classify(request):
    global classifier
    if classifier is None:
        classifier = Classifier(
            ClassifierOptions(
                saved_model_path=os.path.join(
                    'trainer', 'isthemountainout.h5'),
                save_labels_file=os.path.join(
                    'trainer', 'savelabels.txt'),
            )
        )

    classification, confidence, image = classifier.classify(__download_image(
        "http://backend.roundshot.com/cams/241/original"))
    branded_image = __brand_image(image)

    data = request.get_json(force=True)
    state = __get_last_classification(data['bucket'])
    if state != classification:
        __update_last_classification(data['bucket'], state=classification)

    __update_last_image(data['bucket'], image=branded_image)

    if state != classification and classification != 'Night':
        print('Posting image to twitter!')
        __tweet(key_bucket_location=data['bucket'], tweet_status=__get_tweet_message(
            classification), image=branded_image)

    return f'{classification} {confidence:.2f}%'


def __download_image(url: str, *, to_file: str = TEMP_DOWNLOAD_IMAGE) -> str:
    # download an image and place it in a temporary file
    request = requests.get(url, stream=True)
    if request.status_code == 200:
        request.raw.decode_content = True
        with open(to_file, 'wb') as f:
            shutil.copyfileobj(request.raw, f)

        return to_file
    else:
        raise IOError('Could not download latest image')


def __brand_image(image: Image.Image) -> Image.Image:
    global branding
    if branding is None:
        branding = Image.open(os.path.join(
            'branding', 'branding_1920x1080.png'))

    image = image.crop((7036, 162, 8956, 1242))
    image.paste(branding, (0, 0), branding)
    return image


def __get_last_classification(bucket: str) -> Optional[str]:
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.get_blob(STATE_FILE)
    if not blob:
        return None
    else:
        return blob.download_as_string().decode('utf-8').strip()


def __update_last_classification(bucket: str, *, state: str) -> None:
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.get_blob(STATE_FILE)
    if blob is None:
        blob = storage.blob.Blob(STATE_FILE, bucket)
    blob.upload_from_string(state)


def __update_last_image(bucket: str, *, image: Image.Image) -> None:
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.get_blob(IMAGE_FILE)
    if blob is None:
        blob = storage.blob.Blob(IMAGE_FILE, bucket)

    with io.BytesIO() as output:
        image.save(output, format="PNG")
        blob.upload_from_string(output.getvalue())


class ApiKeys:
    consumer_key: str
    consumer_secret_key: str
    access_token: str
    access_token_secret: str

    def __init__(self, *, consumer_key: str, consumer_key_secret: str, access_token: str, access_token_secret: str):
        self.consumer_key = consumer_key
        self.consumer_secret_key = consumer_key_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret


def __tweet(*, key_bucket_location: str, tweet_status: str, image: Image.Image):
    global twitter_keys
    if twitter_keys is None:
        twitter_keys = __load_twitter_keys(key_bucket_location)

    auth = tweepy.OAuthHandler(
        twitter_keys.consumer_key, twitter_keys.consumer_secret_key)
    auth.set_access_token(twitter_keys.access_token,
                          twitter_keys.access_token_secret)
    api = tweepy.API(auth)

    image.save(TEMP_TWITTER_IMAGE_POST)
    api.update_with_media(TEMP_TWITTER_IMAGE_POST, tweet_status)


def __get_tweet_message(classification: str) -> str:
    if classification == 'Visible':
        return "It's out!"
    else:
        return "It's hiding :("


def __load_twitter_keys(bucket: str) -> ApiKeys:
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.get_blob(TWITTER_KEYS_FILE)
    keys = json.loads(blob.download_as_string().decode('utf-8'))
    return ApiKeys(
        consumer_key=keys['consumer_key'],
        consumer_key_secret=keys['consumer_key_secret'],
        access_token=keys['access_token'],
        access_token_secret=keys['access_token_secret'],
    )
