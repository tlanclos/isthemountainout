import yaml
import marshmallow
import marshmallow.fields

from marshmallow_oneofschema import OneOfSchema


def mountain_history_bucket_name() -> str:
    return 'mountain-history'


def mountain_history_filename_template() -> str:
    return 'MountRainier-%Y-%m-%dT%H_%M_%S'


def classification_bucket_name() -> str:
    return 'isthemountainout.appspot.com'


def model_bucket_name() -> str:
    return 'isthemountainout.appspot.com'


def model_filename() -> str:
    return 'v2/isthemountainout.h5'


def classification_filename() -> str:
    return 'mountain-history.classifications.json'


def brand_bucket_name() -> str:
    return 'isthemountainout.appspot.com'


def brand_filename() -> str:
    return 'v2/branding_1920x1080.png'


def twitter_api_key_bucket_name():
    return 'isthemountainout.appspot.com'


def twitter_api_key_filename():
    return 'v2/twitter-keys.json'


class FileConfigurationSchema(marshmallow.Schema):
    path = marshmallow.fields.String(required=True)


class DirectoryConfigurationSchema(marshmallow.Schema):
    path = marshmallow.fields.String(required=True)


class BrandConfigurationSchema(marshmallow.Schema):
    file = marshmallow.fields.Nested(FileConfigurationSchema, required=True)


class LiveImageProviderConfigurationSchema(marshmallow.Schema):
    pass


class SnapshotImageProviderConfigurationSchema(marshmallow.Schema):
    directory = marshmallow.fields.Nested(
        DirectoryConfigurationSchema, required=True)


class ImageProviderConfigurationSchema(OneOfSchema):
    type_schemas = {
        'live': LiveImageProviderConfigurationSchema,
        'snapshot': SnapshotImageProviderConfigurationSchema,
    }


class DatabaseProviderConfigurationSchema(OneOfSchema):
    type_schemas = {'sqlite': FileConfigurationSchema}


class ClassifyConfigurationSchema(marshmallow.Schema):
    image_provider = marshmallow.fields.Nested(
        ImageProviderConfigurationSchema, required=True)
    tracker = marshmallow.fields.Nested(
        DatabaseProviderConfigurationSchema, required=True)
    weights = marshmallow.fields.Nested(FileConfigurationSchema, required=True)


class RootConfigurationSchema(marshmallow.Schema):
    brand = marshmallow.fields.Nested(BrandConfigurationSchema, required=True)
    classify = marshmallow.fields.Nested(
        ClassifyConfigurationSchema, required=True)


with open('.test-config/configuration.yaml', 'r') as f:
    data = yaml.safe_load(f)

val = RootConfigurationSchema().load(data)
print(val)
