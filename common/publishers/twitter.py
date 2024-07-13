import tweepy
import io

from dataclasses import dataclass
from common.publishers.publisher import Publisher
from typing import List
from PIL import Image


@dataclass
class TwitterApiKeys:
    consumer_key: str
    consumer_secret_key: str
    access_token: str
    access_token_secret: str


class TwitterPublisher(Publisher):
    keys: TwitterApiKeys

    def __init__(self, *, keys: TwitterApiKeys):
        self.keys = keys

    def _post(self, image: Image.Image, *, status: str, tags: List[str]):
        auth = tweepy.OAuthHandler(
            self.keys.consumer_key,
            self.keys.consumer_secret_key)
        auth.set_access_token(
            self.keys.access_token,
            self.keys.access_token_secret)
        api = tweepy.API(auth)
        client = tweepy.Client(
            consumer_key=self.keys.consumer_key,
            consumer_secret=self.keys.consumer_secret_key,
            access_token=self.keys.access_token,
            access_token_secret=self.keys.access_token_secret)
        hashtags = ' '.join([f'#{tag}' for tag in tags])
        print(f'Posting "{status}" with tags {hashtags}')

        with io.BytesIO() as output:
            image.save(output, format='PNG')
            output.seek(0)
            media = api.media_upload(None, file=output)
            client.create_tweet(text='\n'.join(
                [status, hashtags]), media_ids=[media.media_id])
