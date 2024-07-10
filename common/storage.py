import os
from io import BytesIO
from PIL import Image
from datetime import datetime
from google.cloud import storage
from common.config import mountain_history_filename_template
from typing import List


class File:
    def read(self) -> bytes:
        pass

    def date(self) -> datetime:
        pass


class GcpFile(File):
    blob: storage.Blob

    def __init__(self, *, blob: storage.Blob) -> None:
        self.blob = blob

    def read(self) -> bytes:
        return self.blob.download_as_string()

    def date(self) -> datetime:
        return datetime.strptime(
            os.path.splitext(self.blob.name)[0],
            mountain_history_filename_template())


class Storage:
    def save_image(self, image: Image.Image, *, filename: str):
        pass

    def list_files(self, directory) -> List[File]:
        pass

    def get(self, filename: str) -> File:
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

    def list_files(self, directory: str) -> List[File]:
        return [GcpFile(blob=blob) for blob in self.client.list_blobs(self.bucket_name, prefix=directory)]

    def get(self, filename: str) -> File:
        return GcpFile(blob=self.bucket.get_blob(filename))

    def get_image(self, filename: str) -> Image.Image:
        blob = self.get(filename)
        return Image.open(BytesIO(blob.download_as_bytes()))

    def rename(self, blob: storage.Blob, *, name: str) -> None:
        self.bucket.rename_blob(blob, name)
