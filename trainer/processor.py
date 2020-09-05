import os
from functools import cached_property, lru_cache
from PIL import Image

from trainer.common.path import unclassified_dir_name
from trainer.common import savestate
from typing import Dict


class CroppingOptions:
    x: int
    y: int
    width: int
    height: int

    def __init__(self, *, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class ProcessorOptions:
    save_state_file: str
    training_data_dir: str
    cropping_options: CroppingOptions

    def __init__(self, *, save_state_file: str, training_data_dir: str, cropping_options: CroppingOptions):
        self.save_state_file = save_state_file
        self.training_data_dir = training_data_dir
        self.cropping_options = cropping_options


class Processor:
    options: ProcessorOptions

    def __init__(self, options: ProcessorOptions):
        self.options = options

    def process(self, filepath: str) -> None:
        state = self.__savestate
        filename = os.path.basename(filepath)
        classification_path = self.__classification_path(filename)
        final_path = os.path.join(classification_path, filename)

        if not os.path.exists(final_path):
            processed = self.__crop(Image.open(filepath))
            os.makedirs(classification_path, exist_ok=True)
            processed.save(final_path)

    def __crop(self, image: Image) -> Image:
        cropping_options = self.options.cropping_options
        return image.crop((
            cropping_options.x,
            cropping_options.y,
            cropping_options.x + cropping_options.width,
            cropping_options.y + cropping_options.height
        ))

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
