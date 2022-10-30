from datetime import datetime, date as Date
from common.image import SpaceNeedleImageProvider, ImageEditor
from common.storage import GcpBucketStorage
from common.config import mountain_history_bucket_name, mountain_history_filename_template
import pytz

PACIFIC_TIMEZONE = pytz.timezone('US/Pacific')


def today() -> Date:
    now = datetime.now(PACIFIC_TIMEZONE)
    return now.date()


def main(request):
    image_provider = SpaceNeedleImageProvider()
    image, date = image_provider.get()
    image = ImageEditor(image).crop(
        x=7036, y=162, width=1920, height=1080).image
    date_str = date.strftime('%B %d %Y')
    today_str = date.strftime('%B %d %Y')
    if today() != date.date():
        f'Image date [{date_str}] and today {today_str} do not match, not storing image.', 412
    else:
        storage = GcpBucketStorage(bucket_name=mountain_history_bucket_name())
        storage.save_image(image, filename=date.strftime(
            mountain_history_filename_template()))
        return '', 200


if __name__ == '__main__':
    main(None)
