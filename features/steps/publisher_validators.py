from behave import *


@then('the image will{condition}be posted')
def image_posted_checker(context, condition: str):
    should_be_posted = condition.strip() != 'not'
    has_posts = len(context.publisher.post_queue)
    assert has_posts == should_be_posted
