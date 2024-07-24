from behave import *

from common.classification import ClassificationRow, ClassificationTracker
from common.frozenmodel import Label


@when('the latest classification is {classification:w}')
def add_classification(context, classification: str):
    assert isinstance(context.classification_tracker, ClassificationTracker)

    context.classification_tracker.amend(
        ClassificationRow(date=context.today, classification=Label(
            classification.capitalize()), should_post=True, was_posted=True))
