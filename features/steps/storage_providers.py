
from tempfile import TemporaryDirectory

from behave import *

from common.storage import LocalFileStorage


@given('a disk storage')
def provide_disk_storage(context):
    temp_directory = TemporaryDirectory()
    context.add_cleanup(temp_directory.cleanup)
    context.storage = LocalFileStorage(base_path=temp_directory.name)
