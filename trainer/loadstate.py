import os

from functools import cached_property
from trainer.common import savestate

from typing import Dict


class LoadStateOptions:
    saved_state_file: str
    training_data_dir: str

    def __init__(self, *, saved_state_file: str, training_data_dir: str):
        self.saved_state_file = saved_state_file
        self.training_data_dir = training_data_dir


class LoadState:
    options: LoadStateOptions

    def __init__(self, options: LoadStateOptions):
        self.options = options

    def load(self):
        state = self.__savestate
        self.__unclassify_all()
        self.__classify(state)

    def __unclassify_all(self):
        if not os.path.exists(self.__unclassified_dir):
            os.mkdir(self.__unclassified_dir)
        classifications = os.listdir(self.options.training_data_dir)
        classifications.remove(os.path.basename(self.__unclassified_dir))

        for classification in classifications:
            class_dir = os.path.join(
                self.options.training_data_dir, classification)
            for filename in os.listdir(class_dir):
                os.rename(os.path.join(class_dir, filename),
                          os.path.join(self.__unclassified_dir, filename))

    def __classify(self, state: Dict[str, str]):
        for filename, classification in state.items():
            class_dir = os.path.join(
                self.options.training_data_dir, classification)
            if not os.path.exists(class_dir):
                os.mkdir(class_dir)
            os.rename(os.path.join(self.__unclassified_dir, filename),
                      os.path.join(class_dir, filename))

        # cleanup empty label directory so that training doesn't consider them
        for dir in os.listdir(self.options.training_data_dir):
            if len(os.listdir(os.path.join(self.options.training_data_dir, dir))) == 0:
                os.rmdir(os.path.join(self.options.training_data_dir, dir))

    @cached_property
    def __unclassified_dir(self) -> str:
        return os.path.join(self.options.training_data_dir, 'Unclassified')

    @cached_property
    def __savestate(self) -> Dict[str, str]:
        if os.path.exists(self.options.saved_state_file):
            return savestate.load(self.options.saved_state_file)
        else:
            raise IOError(f'{self.options.saved_state_file} is empty')
