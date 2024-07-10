import argparse
import os
from datetime import datetime, date as Date
from enum import Enum
from PIL import Image
from common.image import SpaceNeedleImageProvider
from common.storage import GcpBucketStorage
from common.config import mountain_history_bucket_name, mountain_history_filename_template
import pytz
from typing import Optional

PACIFIC_TIMEZONE = pytz.timezone('US/Pacific')


class ImageSink(Enum):
    CLOUD = 'cloud'
    LOCAL = 'local'

    def store(self, *, image: Image.Image, date: datetime, local_output_path: Optional[str]) -> None:
        filename = date.strftime(mountain_history_filename_template())
        if self == ImageSink.CLOUD:
            storage = GcpBucketStorage(
                bucket_name=mountain_history_bucket_name())
            storage.save_image(image, filename=filename)
        elif self == ImageSink.LOCAL:
            with open(os.path.join(local_output_path, f'{filename}.png'), 'wb') as f:
                image.save(f, format='PNG')
        else:
            print(f'Unknown image sink {self}')
            raise Exception(f'Unknown image sink {self}')


parser = argparse.ArgumentParser(
    description='Snapshot an image of Mount Rainier')
subparsers = parser.add_subparsers(dest='sink')
subparsers.add_parser(
    ImageSink.CLOUD.value,
    help='Stores the captured image to the cloud')
local_parser = subparsers.add_parser(
    ImageSink.LOCAL.value,
    help='Stores the captured image to the local filesystem')
local_parser.add_argument(
    '--local-output-path',
    required=True,
    help='If a local sink is chosen, this specifies where the output image is stored on the filesystem')


def today() -> Date:
    now = datetime.now(PACIFIC_TIMEZONE)
    return now.date()


def main(request):
    req = request.json
    image_provider = SpaceNeedleImageProvider()
    image, date = image_provider.get()
    date_str = date.strftime('%B %d %Y')
    today_str = date.strftime('%B %d %Y')
    if today() != date.date():
        f'Image date [{date_str}] and today {today_str} do not match, not storing image.', 412
    else:
        sink = ImageSink(req.get('sink'))
        sink.store(image=image, date=date,
                   local_output_path=req.get('local_output_path', None))
        return '', 200


if __name__ == '__main__':
    args = parser.parse_args()

    class FakeRequest:
        @property
        def json(self):
            return {
                'sink': args.sink,
                'local_output_path': args.local_output_path
            }
    main(FakeRequest())
