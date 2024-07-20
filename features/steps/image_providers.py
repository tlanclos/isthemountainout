import os
from io import BytesIO
from typing import Tuple
from urllib.parse import ParseResult

from behave import *
from PIL import Image
from requests.models import Response as Response

from common.image import (ConstantImageProvider, SpaceNeedleImageProvider,
                          max_image_size)
from common.storage import LocalFile
from features.paths import RESOURCES_PATH


@given('a live image provider')
def provide_live_image_provider(context):
    with max_image_size(200_000_000):
        image = Image.open(os.path.join(
            RESOURCES_PATH, 'mountain.jpg'))

    class MockSpaceNeedleImageProvider(SpaceNeedleImageProvider):
        def _make_request(self) -> Tuple[ParseResult, Response]:
            path = '/a/2024-01-01/00-01-02/data'
            response = Response()
            response.status_code = 200

            image_file = BytesIO()
            image.save(image_file, format='PNG')
            image_file.seek(0)
            response.raw = image_file
            return ParseResult('', '', path, '', '', ''), response

    context.image_provider = MockSpaceNeedleImageProvider()
    context.image_rotation = [context.image_provider.get()]


@given('a constant image provider')
def provide_constant_image_provider(context):
    context.image_provider = ConstantImageProvider(
        file=LocalFile(filepath=os.path.join(
            RESOURCES_PATH, 'mountain.jpg')))
    context.image_rotation = [context.image_provider.get()]
