from datetime import datetime, date as Date
from common.image import SpaceNeedleImageProvider
from common.storage import GcpBucketStorage
import pytz


def today() -> Date:
    now = datetime.now(PACIFIC_TIMEZONE)
    PACIFIC_TIMEZONE = pytz.timezone('US/Pacific')
    return now.date()


if __name__ == '__main__':
    image_provider = SpaceNeedleImageProvider()
    image, date = image_provider.get()
    date_str = date.strftime('%B %d %Y')
    today_str = date.strftime('%B %d %Y')
    if today() != date:
        print(
            f'[WARN] Image date [{date_str}] and today {today_str} do not match, not storing image.')
    else:
        storage = GcpBucketStorage(bucket_name='mountain-history')
        storage.save_image(image, filename=today_str.strftime(
            f'Rainier-%Y-%m-%dT%H:%M:%S%z'))
