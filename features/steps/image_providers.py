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
    date_iso = context.today.strftime('%Y-%m-%d')
    time_iso = context.today.strftime('%H-%M-%S')
    print(date_iso, time_iso)
    with max_image_size(200_000_000):
        image = Image.open(os.path.join(
            RESOURCES_PATH, 'mountain.jpg'))

    class MockSpaceNeedleImageProvider(SpaceNeedleImageProvider):
        def _make_request(self) -> Tuple[ParseResult, Response]:
            path = f'/a/{date_iso}/{time_iso}/data'
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


@given('an image that classifies as "{classification:w}"')
def provide_constant_image_provider_for_classification(context, classification: str):
    context.image_provider = ConstantImageProvider(
        file=LocalFile(filepath=os.path.join(
            RESOURCES_PATH, f'mountain_{classification.lower()}.png')))
    context.image_rotation = [context.image_provider.get()]
