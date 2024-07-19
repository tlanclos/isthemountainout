import random
from datetime import datetime, timezone
from sqlite3 import ProgrammingError
from typing import List

from PIL import Image

from common.frozenmodel import Label

PUBLISHER_STATUSES = {
    Label.BEAUTIFUL: [
        'It\'s beautiful <3',
        'Such a beauty <3',
        'Breathtaking!',
    ],
    Label.MYSTICAL: [
        'It\'s out!',
        'Let it be seen!',
        'Stealth mode lifted!',
    ],
    Label.HIDDEN: [
        'It\'s hiding :(',
        'It\'s under cover',
        'It\'s in stealth mode',
        'Can\'t see it today!',
        'It\'s cloak has been activated',
    ],
}


class Publisher:
    def _post(self, image: Image.Image, *, status: str, tags: List[str]):
        pass

    def post(self, *, image: Image.Image, classification: Label):
        status = self._status_for_classification(classification)
        tags = self._tags_for_classification(classification)
        self._post(image, status=status, tags=tags)

    def _status_for_classification(self, classification: Label) -> str:
        days_since_epoch = (datetime.now(timezone.utc) -
                            datetime(1970, 1, 1)).days
        r = random.Random(days_since_epoch)
        statuses = PUBLISHER_STATUSES.get(classification)
        if isinstance(statuses, list) and len(statuses) > 0:
            return r.choice(statuses)
        raise ProgrammingError(
            f'Must supply some statuses for {classification}')

    def _tags_for_classification(self, classification: Label) -> List[str]:
        if classification == Label.BEAUTIFUL:
            return ['MountRainier', 'SpaceNeedle', 'Seattle']
        return []
