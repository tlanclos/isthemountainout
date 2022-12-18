import json
import tweepy
import io

from common.config import brand_bucket_name, brand_filename, twitter_api_key_bucket_name, twitter_api_key_filename
from common.storage import GcpBucketStorage
from common.frozenmodel import Label
from typing import List
from PIL import Image


class TwitterApiKeys:
    consumer_key: str
    consumer_secret_key: str
    access_token: str
    access_token_secret: str

    def __init__(self, *, consumer_key: str, consumer_key_secret: str, access_token: str, access_token_secret: str):
        self.consumer_key = consumer_key
        self.consumer_secret_key = consumer_key_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret

    @classmethod
    def from_storage(cls):
        print('Loading twitter keys from the cloud')
        bucket = GcpBucketStorage(bucket_name=twitter_api_key_bucket_name())
        blob = bucket.get(twitter_api_key_filename())
        keys = json.loads(blob.download_as_string().decode('utf-8'))
        return TwitterApiKeys(
            consumer_key=keys['consumer_key'],
            consumer_key_secret=keys['consumer_key_secret'],
            access_token=keys['access_token'],
            access_token_secret=keys['access_token_secret'],
        )


class TwitterPoster:
    keys: TwitterApiKeys

    def __init__(self, *, keys: TwitterApiKeys):
        self.keys = keys

    def status_for_label(self, label: Label) -> str:
        if label == Label.BEAUTIFUL:
            return 'It\'s beautiful <3'
        elif label == Label.MYSTICAL:
            return 'It\'s out!'
        else:
            return 'It\'s hiding :('

    def tags_for_label(self, label: Label) -> List[str]:
        if label == Label.BEAUTIFUL:
            return ['MountRainier', 'SpaceNeedle', 'Seattle']
        else:
            return []

    def brand_image(self, image: Image.Image) -> Image.Image:
        print('Loading brand image from the cloud')
        bucket = GcpBucketStorage(bucket_name=brand_bucket_name())
        brand = bucket.get_image(brand_filename())
        branded = image.copy()
        branded.paste(brand, (0, 0), brand)
        return branded

    def post(self, *, status: str, image: Image.Image, tags: List[str]):
        auth = tweepy.OAuthHandler(
            self.keys.consumer_key,
            self.keys.consumer_secret_key)
        auth.set_access_token(
            self.keys.access_token,
            self.keys.access_token_secret)
        api = tweepy.API(auth)

        hashtags = ' '.join([f'#{tag}' for tag in tags])

        image.show()
        with io.BytesIO() as output:
            image.save(output, format='PNG')
            output.seek(0)
            media = api.media_upload(None, file=output)
            api.update_status(
                '\n'.join([status, hashtags]), media_ids=[media.media_id])
