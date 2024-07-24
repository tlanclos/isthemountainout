from behave import *

from common.publishers.mock import MockPublisher


@given('a mock publisher')
def provide_mock_publisher(context):
    context.publisher = MockPublisher()
