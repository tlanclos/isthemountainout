import os
from typing import Tuple
from urllib.parse import ParseResult
from behave import *
from requests.models import Response as Response
from common.image import SpaceNeedleImageProvider, ConstantImageProvider
from PIL import Image
from io import BytesIO
from features.paths import RESOURCES_PATH
from common.storage import LocalFile


@given(u'a live image provider')
def provide_live_image_provider(context):
    image = Image.open(os.path.join(
        RESOURCES_PATH, 'mountain.png'))

    class MockSpaceNeedleImageProvider(SpaceNeedleImageProvider):
        def _make_request(self) -> Tuple[ParseResult, Response]:
            path = '/a/2024-01-01/00:01:02/data'
            response = Response()
            response.status_code = 200

            image_file = BytesIO()
            image.save(image_file, format='PNG')
            image_file.seek(0)
            response.raw = image_file
            return ParseResult('', '', path, '', '', ''), response

    context.image_rotation = [image]
    context.image_provider = MockSpaceNeedleImageProvider()


@given(u'a constant image provider')
def provide_constant_image_provider(context):
    image_file = LocalFile(filepath=os.path.join(
        RESOURCES_PATH, 'mountain.png'))

    context.image_rotation = [image_file.as_image()]
    context.image_provider = ConstantImageProvider(file=image_file)
