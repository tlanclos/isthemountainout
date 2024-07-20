from datetime import datetime
from typing import List, Tuple
from unittest import mock

from behave import *
from PIL import Image

from common.classification import (ClassificationRow, ClassificationTracker,
                                   Classifier)
from common.config import RootConfiguration
from common.image import ImageProvider
from common.snapshot import Snapshotter
from snapshot import main as snapshot_main


@when('snapshot is executed')
def execute_snapshot(context):
    _, _today = context.image_rotation[0]

    class NullClassificationTracker(ClassificationTracker):
        def amend(self, classification: ClassificationRow):
            pass

        def read_latest(self, *, count: int) -> List[ClassificationRow]:
            return []

        def read_latest_day(self) -> List[ClassificationRow]:
            return []

    class NullImageProvider(ImageProvider):
        def get(self) -> Tuple[Image.Image, datetime]:
            return Image.new('rgb', (100, 100)), _today

    with mock.patch('common.snapshot.today') as mock_today:
        mock_today.return_value = _today

        snapshot_main(config=RootConfiguration(
            brand=NullImageProvider(),
            classifier=Classifier(
                interpreter=None,
                image_provider=context.image_provider),
            classification_tracker=NullClassificationTracker(),
            snapshotter=Snapshotter(
                image_provider=context.image_provider,
                store=context.storage
            ),
            publishers=[]))
