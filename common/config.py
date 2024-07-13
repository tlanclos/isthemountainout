import marshmallow
import marshmallow.fields
import yaml

from dataclasses import dataclass
from marshmallow_oneofschema import OneOfSchema
from common.image import ImageProvider, SpaceNeedleImageProvider, LatestSnapshotImageProvider, ConstantImageProvider
from common.storage import LocalFile, LocalFileStorage
from common.frozenmodel import generate_model
from common.classification import SqliteClassificationTracker, ClassificationTracker, Classifier
from common.snapshot import Snapshotter
from common.publishers.publisher import Publisher
from common.publishers.twitter import TwitterApiKeys, TwitterPublisher
from typing import List


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
    weights = marshmallow.fields.Nested(FileConfigurationSchema, required=True)

    @marshmallow.post_load
    def provide(self, data, **kwargs):
        return Classifier(
            model=generate_model(weights_filepath=data['weights'].filepath),
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
    consumer_secret_key = marshmallow.fields.String(required=True)
    access_token = marshmallow.fields.String(required=True)
    access_token_secret = marshmallow.fields.String(required=True)

    @marshmallow.post_load
    def provide(self, data, **kwargs):
        return TwitterApiKeys(
            consumer_key=data['consumer_key'],
            consumer_secret_key=data['consumer_secret_key'],
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
        PublisherConfigurationSchema, required=True)

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
    with open(filepath, 'r') as f:
        return schema.load(yaml.safe_load(f))
