from dataclasses import dataclass
from sqlite3 import ProgrammingError
from typing import List

import marshmallow
import marshmallow.fields
import yaml
from marshmallow_oneofschema.one_of_schema import OneOfSchema

from common.classification import (ClassificationTracker, Classifier,
                                   SqliteClassificationTracker)
from common.frozenmodel import load_saved_model
from common.image import (ConstantImageProvider, ImageProvider,
                          LatestSnapshotImageProvider,
                          SpaceNeedleImageProvider)
from common.publishers.publisher import Publisher
from common.publishers.twitter import TwitterApiKeys, TwitterPublisher
from common.snapshot import Snapshotter
from common.storage import LocalFile, LocalFileStorage


@dataclass
class RootConfiguration:
    brand: ImageProvider
    classifier: Classifier
    classification_tracker: ClassificationTracker
    snapshotter: Snapshotter
    publishers: List[Publisher]


class FileConfigurationSchema(marshmallow.Schema):
    path = marshmallow.fields.String(required=True)

    @marshmallow.post_load
    def provide(self, data, **kwargs):
        return LocalFile(filepath=data['path'])


class DirectoryConfigurationSchema(marshmallow.Schema):
    path = marshmallow.fields.String(required=True)

    @marshmallow.post_load
    def provide(self, data, **kwargs):
        return LocalFileStorage(base_path=data['path'])


class BrandImageProviderConfigurationSchema(marshmallow.Schema):
    file = marshmallow.fields.Nested(FileConfigurationSchema, required=True)

    @marshmallow.post_load
    def provide(self, data, **kwargs):
        return ConstantImageProvider(file=data['file'])


class LiveImageProviderConfigurationSchema(marshmallow.Schema):
    @marshmallow.post_load
    def provide(self, data, **kwargs):
        return SpaceNeedleImageProvider()


class SnapshotImageProviderConfigurationSchema(marshmallow.Schema):
    directory = marshmallow.fields.Nested(
        DirectoryConfigurationSchema, required=True)

    @marshmallow.post_load
    def provider(self, data, **kwargs):
        return LatestSnapshotImageProvider(storage=data['directory'])


class ImageProviderConfigurationSchema(OneOfSchema):
    type_schemas = {
        'live': LiveImageProviderConfigurationSchema,
        'snapshot': SnapshotImageProviderConfigurationSchema,
    }


class SqliteClassificationTrackerConfigurationSchema(marshmallow.Schema):
    database = marshmallow.fields.Nested(
        FileConfigurationSchema, required=True)

    @marshmallow.post_load
    def provide(self, data, **kwargs):
        return SqliteClassificationTracker(dbfile=data['database'])


class ClassificationTrackerConfigurationSchema(OneOfSchema):
    type_schemas = {
        'sqlite': SqliteClassificationTrackerConfigurationSchema,
    }


class ClassifierConfigurationSchema(marshmallow.Schema):
    image_provider = marshmallow.fields.Nested(
        ImageProviderConfigurationSchema, required=True)
    model = marshmallow.fields.Nested(FileConfigurationSchema, required=True)

    @marshmallow.post_load
    def provide(self, data, **kwargs):
        interpreter = load_saved_model(model_filepath=data['model'].filepath)
        interpreter.allocate_tensors()
        return Classifier(
            interpreter=interpreter,
            image_provider=data['image_provider']
        )


class SnapshotterConfigurationSchema(marshmallow.Schema):
    image_provider = marshmallow.fields.Nested(
        ImageProviderConfigurationSchema, required=True)
    store = marshmallow.fields.Nested(
        DirectoryConfigurationSchema, required=True)

    @marshmallow.post_load
    def provide(self, data, **kwargs):
        return Snapshotter(
            image_provider=data['image_provider'],
            store=data['store'])


class TwitterApiKeysConfigurationSchema(marshmallow.Schema):
    consumer_key = marshmallow.fields.String(required=True)
    consumer_key_secret = marshmallow.fields.String(required=True)
    access_token = marshmallow.fields.String(required=True)
    access_token_secret = marshmallow.fields.String(required=True)

    @marshmallow.post_load
    def provide(self, data, **kwargs):
        return TwitterApiKeys(
            consumer_key=data['consumer_key'],
            consumer_key_secret=data['consumer_key_secret'],
            access_token=data['access_token'],
            access_token_secret=data['access_token_secret'])


class TwitterPublisherConfigurationSchema(marshmallow.Schema):
    auth = marshmallow.fields.Nested(
        TwitterApiKeysConfigurationSchema, required=True)

    @marshmallow.post_load
    def provide(self, data, **kwargs):
        return TwitterPublisher(keys=data['auth'])


class PublisherConfigurationSchema(OneOfSchema):
    type_schemas = {'twitter': TwitterPublisherConfigurationSchema}


class RootConfigurationSchema(marshmallow.Schema):
    brand = marshmallow.fields.Nested(
        BrandImageProviderConfigurationSchema, required=True)
    classifier = marshmallow.fields.Nested(
        ClassifierConfigurationSchema, required=True)
    classification_tracker = marshmallow.fields.Nested(
        ClassificationTrackerConfigurationSchema, required=True)
    snapshotter = marshmallow.fields.Nested(
        SnapshotterConfigurationSchema, required=True)
    publishers = marshmallow.fields.List(
        marshmallow.fields.Nested(
            PublisherConfigurationSchema), required=True)

    @marshmallow.post_load
    def provide(self, data, **kwargs):
        return RootConfiguration(
            brand=data['brand'],
            classifier=data['classifier'],
            classification_tracker=data['classification_tracker'],
            snapshotter=data['snapshotter'],
            publishers=data['publishers'])


def create_root_config(filepath: str) -> RootConfiguration:
    schema = RootConfigurationSchema()
    with open(filepath, 'r', encoding='utf-8') as f:
        config = schema.load(yaml.safe_load(f))
        if isinstance(config, RootConfiguration):
            return config
        raise ProgrammingError(
            'Schema does not construct a RootConfiguration object')
