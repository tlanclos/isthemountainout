from behave import *
from PIL import ImageChops

from common.storage import Storage


@then('stores an image')
def stores_an_image(context):
    assert isinstance(context.image_rotation, list)
    assert isinstance(context.storage, Storage)

    expected_image, _ = context.image_rotation[0]
    stored_image = context.storage.list_files('.')[0].as_image()
    image_diff = ImageChops.difference(expected_image, stored_image)
    assert not image_diff.getbbox()
