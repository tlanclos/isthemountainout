import os
from io import BytesIO
from PIL import Image
from datetime import datetime
from google.cloud import storage
from common.const import mountain_history_filename_template
from typing import List
from dataclasses import dataclass


class File:
    def filename() -> str:
        pass

    def read(self) -> bytes:
        pass

    def date(self) -> datetime:
        return datetime.strptime(
            os.path.splitext(self.filename())[0],
            mountain_history_filename_template())

    def as_image(self) -> Image.Image:
        return Image.open(BytesIO(self.read()))


class GcpFile(File):
    blob: storage.Blob

    def __init__(self, *, blob: storage.Blob) -> None:
        self.blob = blob

    def filename(self) -> str:
        return self.blob.name

    def read(self) -> bytes:
        return self.blob.download_as_string()


@dataclass
class LocalFile(File):
    filepath: str

    def filename(self) -> str:
        return os.path.basename(self.filepath)

    def read(self) -> bytes:
        with open(self.filepath, 'rb') as f:
            return f.read()


class Storage:
    def save_image(self, image: Image.Image, *, filename: str):
        pass

    def list_files(self, directory: str) -> List[File]:
        pass

    def get(self, filename: str) -> File:
        pass

    def get_image(self, filename: str) -> Image.Image:
        return self.get(filename).as_image()


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
        return [
            GcpFile(blob=blob) for blob in self.client.list_blobs(self.bucket_name, prefix=directory.lstrip('./'))
        ]

    def get(self, filename: str) -> File:
        return GcpFile(blob=self.bucket.get_blob(filename))


@dataclass
class LocalFileStorage(Storage):
    base_path: str

    def save_image(self, image: Image.Image, *, filename: str):
        with open(os.path.join(self.base_path, f'{filename}.png'), 'wb') as f:
            image.save(f, format='PNG')

    def list_files(self, directory: str) -> List[File]:
        listing_directory = os.path.join(self.base_path, directory)
        return [
            LocalFile(filepath=os.path.join(listing_directory, filename)) for filename in os.listdir(listing_directory)
        ]

    def get(self, filename: str) -> File:
        return LocalFile(filepath=os.path.join(self.base_path, filename))
