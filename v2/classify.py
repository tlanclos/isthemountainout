from common.image import ImageProvider, LatestSnapshotImageProvider, SpaceNeedleImageProvider
from trainer.model import generate_model, labels
from common.storage import GcpBucketStorage
from common.config import model_bucket_name, model_filename
from common.weights import weights
from common.classifier import Classifier
import argparse

# provider = LatestSnapshotImageProvider()
# image, date = provider.get()
# print(date)
# image.show()

parser = argparse.ArgumentParser(description='Classify an image of Mount Rainier')
parser.add_argument('source', choices=['live', 'snapshot'], help='Source image provider')
parser.add_argument('--local-weights', help='Set this flag to the path for the local weights filename, unset will load weights from cloud storage')
args = parser.parse_args()

def get_image_provider(source: str) -> ImageProvider:
    if source == 'live':
        return SpaceNeedleImageProvider()
    elif source == 'snapshot':
        return LatestSnapshotImageProvider()
    else:
        print(f'Unknown image source {source}')
        raise Exception(f'Unknown image source {source}')

def get_model():
    if args.local_weights:
        print(f'Loading weight locally from {args.local_weights}')
        return generate_model(weights_filepath=args.local_weights)
    else:
        print(f'Loading weights from the cloud')
        with weights() as filename:
            return generate_model(weights_filepath=filename)

image_provider = get_image_provider(args.source)
classifier = Classifier(model=get_model(), labels=labels())

image, date = image_provider.get()

print(f'Classifying image for date {date}')
print(classifier.classify(image))

