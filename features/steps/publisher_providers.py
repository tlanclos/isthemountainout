from behave import *
from common.publishers.publisher import Publisher
from PIL import Image
from typing import List

from dataclasses import dataclass


class PublishedEntry:
    image: Image.Image
    status: str
    tags: List[str]


class MockPublisher(Publisher):
    post_queue: List[PublishedEntry] = []

    def _post(self, image: Image.Image, *, status: str, tags: List[str]):
        self.post_queue.append(PublishedEntry(
            image=image,
            status=status,
            tags=tags
        ))


@given('a mock publisher')
def provide_mock_publisher(context):
    context.publisher = MockPublisher()
