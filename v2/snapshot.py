from datetime import datetime, date as Date
from common.image import SpaceNeedleImageProvider, crop
from common.storage import GcpBucketStorage
import pytz

PACIFIC_TIMEZONE = pytz.timezone('US/Pacific')


def today() -> Date:
    now = datetime.now(PACIFIC_TIMEZONE)
    return now.date()


if __name__ == '__main__':
    image_provider = SpaceNeedleImageProvider()
    image, date = image_provider.get()
    image = crop(image, x=7036, y=162, width=1920, height=1080)
    date_str = date.strftime('%B %d %Y')
    today_str = date.strftime('%B %d %Y')
    if today() != date:
        print(
            f'[WARN] Image date [{date_str}] and today {today_str} do not match, not storing image.')
    else:
        storage = GcpBucketStorage(bucket_name='mountain-history')
        storage.save_image(image, filename=date.strftime(
            f'MountRainier-%Y-%m-%dT%H:%M:%S%z'))
