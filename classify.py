import argparse
import os

from common.config import RootConfiguration, create_root_config
from common.image import ImageEditor

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


parser = argparse.ArgumentParser(
    description='Classify an image of Mount Rainier')
parser.add_argument(
    '--dry-run',
    action='store_true',
    help='Classify the image and print to the console, but nothing is committed')
parser.add_argument(
    '--config',
    type=create_root_config,
    help='Path to the configuration file')


def main(*, config: RootConfiguration, dry_run: bool = False):
    classifier, tracker = config.classifier, config.classification_tracker
    classification, image = classifier.classify_next()
    print('Classification', classification)

    if tracker.should_post(classification.classification):
        classification.was_posted = True
        print(f'Posting {classification}')
        if not dry_run:
            tracker.amend(classification)
            print('Branding image')
            branded_image = ImageEditor(image).brand(brand=config.brand.get())
            for publisher in config.publishers:
                publisher.post(branded_image, classification=classification)
    else:
        print(f'Classification did not change from {classification}')
        if not dry_run:
            tracker.amend(classification)


if __name__ == '__main__':
    args = parser.parse_args()
    main(config=args.config, dry_run=args.dry_run)
