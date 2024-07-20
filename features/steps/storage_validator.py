from behave import *
from PIL import ImageChops


@then('stores an image')
def stores_an_image(context):
    expected_image, _ = context.image_rotation[0]
    stored_image = context.storage.list_files('.')[0].as_image()
    image_diff = ImageChops.difference(expected_image, stored_image)
    assert not image_diff.getbbox()
