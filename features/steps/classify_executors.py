from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Tuple
from unittest import mock

from behave import *
from PIL import Image

from classify import main as classify_main
from common.classification import Classifier
from common.config import RootConfiguration
from common.image import ImageProvider
from common.snapshot import Snapshotter
from common.storage import LocalFileStorage


@when('classify is executed')
@when('classify is executed {count:d} times')
def execute_classify(context, count: int = 1):
    class NullImageProvider(ImageProvider):
        def get(self) -> Tuple[Image.Image, datetime]:
            return Image.new('RGBA', (100, 100)), context.today

    with mock.patch('common.image.today') as mock_image_today:
        with mock.patch('common.publishers.publisher.today') as mock_publisher_today:
            mock_image_today.return_value = context.today
            mock_publisher_today.return_value = context.today

            with TemporaryDirectory() as tempdir:
                for _ in range(count):
                    classify_main(
                        config=RootConfiguration(
                            brand=NullImageProvider(),
                            classifier=Classifier(
                                interpreter=context.interpreter,
                                image_provider=context.image_provider
                            ),
                            classification_tracker=context.classification_tracker,
                            snapshotter=Snapshotter(
                                image_provider=NullImageProvider(),
                                store=LocalFileStorage(base_path=tempdir)
                            ),
                            publishers=[context.publisher]),
                        post=True)
