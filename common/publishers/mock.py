
from dataclasses import dataclass
from typing import List

from PIL import Image

from common.publishers.publisher import Publisher


@dataclass
class PublishedEntry:
    image: Image.Image
    status: str
    tags: List[str]


class MockPublisher(Publisher):
    post_queue: List[PublishedEntry]

    def __init__(self):
        self.post_queue = []

    def _post(self, image: Image.Image, *, status: str, tags: List[str]):
        self.post_queue.append(PublishedEntry(
            image=image,
            status=status,
            tags=tags
        ))
