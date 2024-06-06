import os
import tempfile

from common.storage import GcpBucketStorage
from common.config import model_bucket_name, model_filename
from contextlib import contextmanager
from typing import Optional


@contextmanager
def weights(local_filename: Optional[str] = None):
    if local_filename:
        print(f'Loading weight locally from {local_filename}')
        yield local_filename
    else:
        print(f'Loading weights from the cloud')
        bucket = GcpBucketStorage(bucket_name=model_bucket_name())
        filename = '/tmp/isthemountainout.h5'
        try:
            blob = bucket.get(model_filename())
            blob.download_to_filename(filename)
            yield filename
        finally:
            os.unlink(filename)
