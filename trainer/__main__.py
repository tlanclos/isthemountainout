import argparse
import os

from trainer.processor import Processor, ProcessorOptions, CroppingOptions
from trainer.savestate import SaveState, SaveStateOptions

from trainer.common.path import get_script_path
from trainer.common import savestate

parser = argparse.ArgumentParser(
    description='Collection of scripts used to process and train a classifier')
subparsers = parser.add_subparsers(
    dest='command', help='Which module should be executed')
parser.add_argument(
    '--save-state', default='savestate.txt', help='Relative path to the savestate file')

processor_parser = subparsers.add_parser(
    'processor', help='Command to process files prior to training')

savestate_parser = subparsers.add_parser(
    'savestate', help='Simple script to save the state of the training data classification'
)
savestate_parser.add_argument(
    '--force', action='store_true', default=False, help='Force overwrite of all values within savestate file; otherwise, amend only'
)

args = parser.parse_args()

if args.command == 'processor':
    processor = Processor(
        ProcessorOptions(
            save_state_file=os.path.join(get_script_path(), args.save_state),
            training_data_dir=os.path.join(get_script_path(), 'TrainingData'),
            cropping_options=CroppingOptions(
                x=7868,
                y=604,
                width=224,
                height=224
            )
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
            training_data_dir=os.path.join(get_script_path(), 'TrainingData'),
            force_overwrite=args.force
        )
    )
    savestate.save()
