from behave import *
from common.classification import ClassificationTracker, ClassificationRow
from typing import List


@given('an in memory classification tracker')
def provide_in_memory_classification_tracker(context):
    class InMemoryClassificationTracker(ClassificationTracker):
        classifications: List[ClassificationRow]

        def __init__(self):
            self.classifications = []

        def amend(self, classification: ClassificationRow):
            self.classifications.append(classification)
            self.classifications.sort(key=lambda c: c.date)

        def read_latest(self, *, count: int) -> List[ClassificationRow]:
            return self.classifications[-count:]

        def read_latest_day(self) -> List[ClassificationRow]:
            return [c for c in self.classifications if c.date >= context.today]

    context.classification_tracker = InMemoryClassificationTracker()
