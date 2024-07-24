from behave import *

from common.publishers.mock import MockPublisher


@then('the image will{condition}be posted')
def image_posted_checker(context, condition: str):
    assert isinstance(context.publisher, MockPublisher)

    should_be_posted = condition.strip() != 'not'
    has_posts = len(context.publisher.post_queue)
    assert has_posts == should_be_posted
