import argparse
import os

from trainer.processor import Processor, ProcessorOptions
from trainer.savestate import SaveState, SaveStateOptions
from trainer.trainer import Trainer, TrainerOptions
from trainer.classifier import Classifier, ClassifierOptions

from trainer.common.path import get_script_path
from trainer.common import savestate

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

savestate_parser = subparsers.add_parser(
    'savestate', help='Simple script to save the state of the training data classification')
savestate_parser.add_argument(
    '--force', action='store_true', default=False, help='Force overwrite of all values within savestate file; otherwise, amend only')

trainer_parser = subparsers.add_parser(
    'trainer', help='Script to train the model')
trainer_parser.add_argument(
    '--visualize', action='store_true', default=False, help='Should plots be shown of the training')

classifier_parser = subparsers.add_parser(
    'classifier', help='Classify an image based on the model')
classifier_parser.add_argument('--image', help='Image to classify')


args = parser.parse_args()

if args.command == 'processor':
    processor = Processor(
        ProcessorOptions(
            save_state_file=os.path.join(get_script_path(), args.save_state),
            training_data_dir=os.path.join(get_script_path(), 'TrainingData'),
        )
    )
    unprocessed_dir = os.path.abspath(os.path.join(
        get_script_path(), '..', 'downloader', 'TrainingData'))
    for filename in os.listdir(unprocessed_dir):
        processor.process(os.path.join(unprocessed_dir, filename))
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
elif args.command == 'trainer':
    trainer = Trainer(
        TrainerOptions(
            data_dir=os.path.join(get_script_path(), 'TrainingData'),
            image_size=(224, 224),
            batch_size=32,
            saved_model_path=os.path.join(
                get_script_path(), 'isthemountainout.h5'),
            visualize=args.visualize
        )
    )
    trainer.train()
elif args.command == 'classifier':
    classifier = Classifier(
        ClassifierOptions(
            saved_model_path=os.path.join(
                get_script_path(), 'isthemountainout.h5'),
            save_labels_file=os.path.join(get_script_path(), args.save_labels),
        )
    )
    print(classifier.classify(args.image))
