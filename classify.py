import argparse
import os

from common.config import RootConfiguration, create_root_config
from common.image import ImageEditor

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


parser = argparse.ArgumentParser(
    description='Classify an image of Mount Rainier')
parser.add_argument(
    '--enable-posting',
    action='store_true',
    help='Classify the image, print to the console, and store the classification result, but nothing is posted to the internet')
parser.add_argument(
    '--config',
    type=create_root_config,
    help='Path to the configuration file')


def main(*, config: RootConfiguration, post: bool = False):
    classifier, tracker = config.classifier, config.classification_tracker
    classification, image = classifier.classify_next()
    print('Classification', classification)

    classification.should_post = tracker.should_post(
        classification.classification)
    if classification.should_post:
        print('Branding image')
        branded_image = ImageEditor(image).brand(brand=config.brand.get())
        classification.was_posted = post
        if classification.was_posted:
            print(f'Posting {classification}')
            for publisher in config.publishers:
                publisher.post(branded_image, classification=classification)

    else:
        print(f'Classification did not change from {classification}')

    print(f'Updating classification log {classification}')
    tracker.amend(classification)


if __name__ == '__main__':
    args = parser.parse_args()
    main(config=args.config, post=args.enable_posting)
