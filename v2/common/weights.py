from common.storage import GcpBucketStorage
from common.config import model_bucket_name, model_filename
from contextlib import contextmanager
import tempfile


@contextmanager
def weights(local: bool = False):
    bucket = GcpBucketStorage(bucket_name=model_bucket_name())
    try:
        blob = bucket.get(model_filename())
        data = blob.download_as_bytes()
        temp = tempfile.NamedTemporaryFile()
        temp.write(data)
        temp.seek(0)
        yield temp.name
    finally:
        temp.close()
