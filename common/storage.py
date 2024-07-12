import os
from io import BytesIO
from PIL import Image
from datetime import datetime
from google.cloud import storage
from common.config import mountain_history_filename_template
from typing import List


class File:
    def filename() -> str:
        pass

    def read(self) -> bytes:
        pass

    def date(self) -> datetime:
        return datetime.strptime(
            os.path.splitext(self.blob.name)[0],
            mountain_history_filename_template())


class GcpFile(File):
    blob: storage.Blob

    def __init__(self, *, blob: storage.Blob) -> None:
        self.blob = blob

    def filename(self) -> str:
        return self.blob.name

    def read(self) -> bytes:
        return self.blob.download_as_string()


class LocalFile(File):
    filepath: str

    def __init__(self, *, filepath: str) -> None:
        self.filepath = filepath

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
        f = self.get(filename)
        return Image.open(BytesIO(f.read()))


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


class LocalFileStorage(Storage):
    base_path: str

    def __init__(self, *, base_path: str) -> None:
        self.base_path = base_path

    def save_image(self, image: Image.Image, *, filename: str):
        with open(os.path.join(self.base_path, filename), 'w') as f:
            image.save(f, format='PNG')

    def list_files(self, directory: str) -> List[File]:
        return [LocalFile(os.path.join(self.base_path, filename)) for filename in os.listdir(directory)]

    def get(self, filename: str) -> File:
        return LocalFile(filepath=os.path.join(self.base_path, filename))
