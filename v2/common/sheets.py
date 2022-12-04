from datetime import datetime
from common.frozenmodel import Label
from typing import List


class ClassificationRow:
    date: datetime
    classification: Label

    def __init__(self, *, date: datetime, classification: Label):
        self.date = date
        self.classification = classification

    def as_list(self) -> List[str]:
        return [self.date.isoformat(), self.classification.value]

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(date={self.date.isoformat()} classification={self.classification.value})'
