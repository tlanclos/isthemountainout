import os
from functools import cached_property, lru_cache
from PIL import Image

from trainer.common.path import unclassified_dir_name
from trainer.common import savestate, model
from typing import Dict


class ProcessorOptions:
    save_state_file: str
    training_data_dir: str

    def __init__(self, *, save_state_file: str, training_data_dir: str):
        self.save_state_file = save_state_file
        self.training_data_dir = training_data_dir


class Processor:
    options: ProcessorOptions

    def __init__(self, options: ProcessorOptions):
        self.options = options

    def process(self, filepath: str, *, algorithm: str = 'default') -> None:
        state = self.__savestate
        filename = os.path.basename(filepath)
        classification_path = self.__classification_path(filename)
        final_path = os.path.join(classification_path, filename)

        if not os.path.exists(final_path):
            processed = model.image_preprocessor(
                Image.open(filepath), algorithm=algorithm)
            os.makedirs(classification_path, exist_ok=True)
            processed.save(final_path)

    @lru_cache(maxsize=4)
    def __classification_path(self, filename: str) -> str:
        state = self.__savestate
        if filename in state:
            return os.path.join(self.options.training_data_dir, state[filename])
        else:
            return os.path.join(self.options.training_data_dir, unclassified_dir_name())

    @cached_property
    def __savestate(self) -> Dict[str, str]:
        if os.path.exists(self.options.save_state_file):
            return savestate.load(self.options.save_state_file)
        else:
            return {}
