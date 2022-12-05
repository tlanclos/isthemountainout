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
        try:
            blob = bucket.get(model_filename())
            f = tempfile.NamedTemporaryFile(delete=False)
            f.write(blob.download_as_bytes())
            yield f.name
        finally:
            f.close()
            os.unlink(f.name)
