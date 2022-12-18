from io import BytesIO
from PIL import Image
from google.cloud import storage
from typing import List


class Storage:
    def save_image(self, image: Image.Image, *, filename: str):
        pass

    def list_files(self, directory) -> List[storage.Blob]:
        pass

    def get(self, filename: str) -> storage.Blob:
        pass

    def get_image(self, filename: str) -> Image.Image:
        pass


class GcpBucketStorage(Storage):
    bucket_name: str
    client: storage.Client
    bucket: storage.Bucket

    def __init__(self, *, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.get_bucket(self.bucket_name)

    def save_image(self, image: Image.Image, *, filename: str):
        blob = self.bucket.blob(f'{filename}.png')
        imagefile = BytesIO()
        image.save(imagefile, format='PNG')
        blob.upload_from_string(imagefile.getvalue())

    def list_files(self, directory: str) -> List[storage.Blob]:
        return list(self.client.list_blobs(self.bucket_name, prefix=directory))

    def get(self, filename: str) -> storage.Blob:
        return self.bucket.get_blob(filename)

    def get_image(self, filename: str) -> Image.Image:
        blob = self.get(filename)
        return Image.open(BytesIO(blob.download_as_bytes()))
