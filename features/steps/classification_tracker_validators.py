import sys

from behave import *

from common.classification import ClassificationTracker
from common.frozenmodel import Label


@then('the latest tracked classification is "{classification:w}"')
def latest_classification_is(context, classification: str):
    assert isinstance(context.classification_tracker, ClassificationTracker)

    latest_classification = next(
        iter(context.classification_tracker.read_latest(count=1)), None)

    assert latest_classification is not None
    assert latest_classification.classification == Label(classification)


@then('the image should{condition}be posted')
def image_should_be_posted_checker(context, condition: str):
    assert isinstance(context.classification_tracker, ClassificationTracker)

    should_be_posted = condition.strip() != 'not'
    any_should_posts = any(map(lambda c: c.should_post, context.classification_tracker.read_latest(
        count=sys.maxsize)))
    assert any_should_posts == should_be_posted
