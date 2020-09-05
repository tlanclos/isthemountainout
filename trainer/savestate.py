import os

from functools import cached_property
from trainer.common import savestate
from trainer.common.path import unclassified_dir_name

from typing import Dict


class SaveStateOptions:
    save_state_file: str
    training_data_dir: str
    force_overwrite: bool

    def __init__(self, *, save_state_file: str, training_data_dir: str, force_overwrite: bool):
        self.save_state_file = save_state_file
        self.training_data_dir = training_data_dir
        self.force_overwrite = force_overwrite


class SaveState:
    options: SaveStateOptions

    def __init__(self, options: SaveStateOptions):
        self.options = options

    def save(self) -> None:
        state = self.__savestate
        classification_paths = [path for path in os.listdir(
            self.options.training_data_dir) if path != unclassified_dir_name()]
        for d in classification_paths:
            for filename in os.listdir(os.path.join(self.options.training_data_dir, d)):
                if filename not in state or self.options.force_overwrite:
                    state[filename] = d

        with open(self.options.save_state_file, 'w') as f:
            f.writelines(
                [f'{filename} {classification}\n' for filename, classification in state.items()])

    @cached_property
    def __savestate(self) -> Dict[str, str]:
        if os.path.exists(self.options.save_state_file):
            return savestate.load(self.options.save_state_file)
        else:
            return {}
