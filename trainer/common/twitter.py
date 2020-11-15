import tweepy
from PIL import Image
from common.frozenmodel import Label


TEMP_TWITTER_IMAGE_POST = '/tmp/image-to-tweet.png'


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


def tweet(*, keys: ApiKeys, tweet_status: str, image: Image):
    auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret_key)
    auth.set_access_token(keys.access_token, keys.access_token_secret)
    api = tweepy.API(auth)

    image.save(TEMP_TWITTER_IMAGE_POST)
    api.update_with_media(TEMP_TWITTER_IMAGE_POST, tweet_status)


def message_for(classification: Label) -> str:
    if classification == Label.BEAUTIFUL:
        return "It's beautiful <3"
    elif classification == Label.MYSTICAL:
        return "It's out!"
    else:
        return "It's hiding :("
