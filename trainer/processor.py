import os
import sys
import argparse
from PIL import Image

parser = argparse.ArgumentParser(
    description='Process currently unprocessed images and classify them based off savestate file, unclassified images will be placed in an Unclassified directory')
parser
parser.add_argument(
    '-i', '--input', default='savestate.txt', help='Input savestate filename')
parser.add_argument('--unclassified-directory', default='Unclassified',
                    help='If an image is not yet classified, store it in this directory')
args = parser.parse_args()

SCRIPT_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))
UNPROCESSED_DIR = os.path.abspath(
    f'{SCRIPT_PATH}/../downloader/TrainingData/Unprocessed')
TRAINING_DATA_DIR = os.path.abspath(f'{SCRIPT_PATH}/TrainingData')
SAVESTATE_FILE = os.path.join(SCRIPT_PATH, args.input)
CROPPED_LOCATION = (7868, 604)
SIZE = (224, 224)

state = {}
if os.path.exists(SAVESTATE_FILE):
    with open(SAVESTATE_FILE, 'r') as f:
        for line in f.readlines():
            filename, _, classification = line.strip().partition(' ')
            state[filename] = classification

for filename in os.listdir(UNPROCESSED_DIR):
    full_path = os.path.join(UNPROCESSED_DIR, filename)
    print(f'Processing {full_path}')
    im = Image.open(full_path)
    cropped = im.crop((
        CROPPED_LOCATION[0], CROPPED_LOCATION[1],
        CROPPED_LOCATION[0] + SIZE[0],
        CROPPED_LOCATION[1] + SIZE[1]))

    if filename in state:
        classified_path = os.path.join(TRAINING_DATA_DIR, state[filename])
    else:
        classified_path = os.path.join(
            TRAINING_DATA_DIR, args.unclassified_directory)

    if not os.path.exists(classified_path):
        os.makedirs(classified_path, exist_ok=True)

    cropped.save(os.path.join(classified_path, filename))
