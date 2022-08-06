from io import BytesIO
from PIL import Image
from google.cloud import storage


class Storage:
    def save_image(self, image: Image.Image, *, filename: str):
        pass


class GcpBucketStorage(Storage):
    bucket: storage.Bucket

    def __init__(self, *, bucket_name: str):
        client = storage.Client()
        self.bucket = client.get_bucket(bucket_name)

    def save_image(self, image: Image.Image, *, filename: str):
        blob = self.bucket.blob(f'{filename}.png')
        imagefile = BytesIO()
        image.save(imagefile, format='PNG')
        blob.upload_from_string(imagefile.getvalue())
