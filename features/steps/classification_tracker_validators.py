import sys

from behave import *

from common.classification import ClassificationTracker
from common.frozenmodel import Label


@then('the latest tracked classification is {classification:w}')
def latest_classification_is(context, classification: str):
    assert isinstance(context.classification_tracker, ClassificationTracker)

    latest_classification = next(
        iter(context.classification_tracker.read_latest(count=1)), None)

    assert latest_classification is not None
    assert latest_classification.classification == Label(
        classification.capitalize())


@then('the image should{condition}be posted')
def image_should_be_posted_checker(context, condition: str):
    assert isinstance(context.classification_tracker, ClassificationTracker)

    should_be_posted = condition.strip() != 'not'
    any_should_posts = any(map(lambda c: c.should_post, context.classification_tracker.read_latest(
        count=sys.maxsize)))
    assert any_should_posts == should_be_posted


@then('the classification, {classification:w}, was posted exactly once')
def classification_is_only_posted_once(context, classification: str):
    assert isinstance(context.classification_tracker, ClassificationTracker)

    posted_classifications = [
        c for c in context.classification_tracker.read_latest(
            count=sys.maxsize) if c.was_posted and c.classification == Label(classification.capitalize())]
    print(posted_classifications)

    assert len(posted_classifications) == 1


@then('the classification, {classification:w}, was never posted')
def classification_is_never_posted(context, classification: str):
    assert isinstance(context.classification_tracker, ClassificationTracker)

    posted_classifications = [
        c for c in context.classification_tracker.read_latest(
            count=sys.maxsize) if c.was_posted and c.classification == Label(classification.capitalize())]

    assert len(posted_classifications) == 0
