import time
import tensorflow as tf
from typing import Tuple


class Dataset:
    directory: str
    batch_size: int
    image_size: Tuple[int, int]
    training: tf.data.Dataset
    validation: tf.data.Dataset
    seed: int

    def __init__(self, directory: str, *, batch_size=32, image_size=(1920, 1080)):
        self.seed = int(time.time())
        self.directory = directory
        self.batch_size = batch_size
        self.image_size = image_size

        self.training = self.dataset_for('training')
        self.validation = self.dataset_for('validation')

    def dataset_for(self, subset: str):
        return tf.keras.utils.image_dataset_from_directory(
            self.directory,
            label_mode='categorical',
            seed=self.seed,
            validation_split=0.2,
            subset=subset,
            batch_size=self.batch_size,
            image_size=self.image_size,
        )
