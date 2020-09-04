import os
import sys
import argparse

parser = argparse.ArgumentParser(
    description='Process currently classified images into a saved state file')
parser.add_argument(
    '-o', '--output', default='savestate.txt', help='Output filename')
parser.add_argument('--force-override', action='store_true', default=False,
                    help='Force overwriting savestate file')
args = parser.parse_args()

SCRIPT_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))
SAVESTATE_FILE = os.path.join(SCRIPT_PATH, args.output)
TRAINING_DIR = os.path.join(SCRIPT_PATH, 'TrainingData')
UNCLASSIFIED_DIR = os.path.join(TRAINING_DIR, 'Unclassified')
CLASSIFIED_DIRS = {d for d in os.listdir(
    TRAINING_DIR) if d != os.path.basename(UNCLASSIFIED_DIR)}

state = {}
if os.path.exists(SAVESTATE_FILE):
    with open(SAVESTATE_FILE, 'r') as f:
        for line in f.readlines():
            filename, _, classification = line.strip().partition(' ')
            state[filename] = classification

with open(SAVESTATE_FILE, 'w') as f:
    for d in CLASSIFIED_DIRS:
        for filename in os.listdir(os.path.join(TRAINING_DIR, d)):
            if filename not in state or args.force_override:
                state[filename] = os.path.basename(d)
            else:
                print(f'not overriding classification of {filename}')

    f.writelines([f'{key} {value}\n' for key, value in state.items()])
