import argparse
import os
import glob

from trainer.processor import Processor, ProcessorOptions
from trainer.savestate import SaveState, SaveStateOptions
from trainer.loadstate import LoadState, LoadStateOptions
from trainer.trainer import Trainer, TrainerOptions
from trainer.classifier import Classifier, ClassifierOptions

from trainer.common.path import get_script_path
from trainer.common import savestate
from PIL import Image

parser = argparse.ArgumentParser(
    description='Collection of scripts used to process and train a classifier')
subparsers = parser.add_subparsers(
    dest='command', help='Which module should be executed')
parser.add_argument(
    '--save-state', default='savestate.txt', help='Relative path to the savestate file')
parser.add_argument(
    '--save-labels', default='savelabels.txt', help='Relative path to the savelabels file')

processor_parser = subparsers.add_parser(
    'processor', help='Command to process files prior to training')
processor_parser.add_argument(
    '--prior', action='store_true', default=False, help='When set, prior training data will be processed (this is not often used, so default is False)')

savestate_parser = subparsers.add_parser(
    'savestate', help='Simple script to save the state of the training data classification')
savestate_parser.add_argument(
    '--force', action='store_true', default=False, help='Force overwrite of all values within savestate file; otherwise, amend only')

loadstate_parser = subparsers.add_parser(
    'loadstate', help='Simple script to load a previous training directory state')

trainer_parser = subparsers.add_parser(
    'trainer', help='Script to train the model')
trainer_parser.add_argument(
    '--visualize', action='store_true', default=False, help='Should plots be shown of the training')
trainer_parser.add_argument(
    '--disallow-memory-growth', action='store_true', default=False, help='Disallow memory to grow on your GPUs')

classifier_parser = subparsers.add_parser(
    'classifier', help='Classify an image based on the model')
classifier_parser.add_argument('--image', help='Image to classify')
classifier_parser.add_argument(
    '--show', action='store_true', default=False, help='Show the image being classified')
classifier_parser.add_argument(
    '--preprocess-algorithm', default='default', help='Algorithm to use to preprocess images')


args = parser.parse_args()

if args.command == 'processor':
    processor = Processor(
        ProcessorOptions(
            save_state_file=os.path.join(get_script_path(), args.save_state),
            training_data_dir=os.path.join(get_script_path(), 'TrainingData'),
        )
    )
    unprocessed_dir = os.path.abspath(os.path.join(
        get_script_path(), '..', 'downloader', 'TrainingData' if not args.prior else 'TrainingDataPrior'))
    for filename in os.listdir(unprocessed_dir):
        processor.process(os.path.join(unprocessed_dir, filename),
                          algorithm='prior' if args.prior else 'default')
elif args.command == 'savestate':
    savestate = SaveState(
        SaveStateOptions(
            save_state_file=os.path.join(get_script_path(), args.save_state),
            save_labels_file=os.path.join(get_script_path(), args.save_labels),
            training_data_dir=os.path.join(get_script_path(), 'TrainingData'),
            force_overwrite=args.force
        )
    )
    savestate.save()
elif args.command == 'loadstate':
    loadstate = LoadState(
        LoadStateOptions(
            saved_state_file=os.path.join(get_script_path(), args.save_state),
            training_data_dir=os.path.join(get_script_path(), 'TrainingData'),
        )
    )
    loadstate.load()
elif args.command == 'trainer':
    trainer = Trainer(
        TrainerOptions(
            data_dir=os.path.join(get_script_path(), 'TrainingData'),
            image_size=(224, 224),
            batch_size=32,
            saved_model_path=os.path.join(
                get_script_path(), 'isthemountainout.h5'),
            visualize=args.visualize,
            allow_memory_growth=not args.disallow_memory_growth,
        )
    )
    trainer.train()
elif args.command == 'classifier':
    classifier = Classifier(
        ClassifierOptions(
            saved_model_path=os.path.join(
                get_script_path(), 'isthemountainout.h5'),
            save_labels_file=os.path.join(get_script_path(), args.save_labels),
            preprocess_algorithm=args.preprocess_algorithm,
        )
    )
    for filename in glob.iglob(args.image):
        classification, confidence, image = classifier.classify(filename)
        print(filename, classification, confidence)
        if args.show:
            image = image.crop((7036, 162, 8956, 1242))
            branding = Image.open(os.path.join(
                get_script_path(), '..', 'branding', 'branding_1920x1080.png'))
            image.paste(branding, (0, 0), branding)
            image.show()
