from functools import cached_property

import tensorflow as tf
import tensorflow_hub as hub
from tensorflow.python.keras.preprocessing.image import DirectoryIterator

from trainer.common import model


class TrainerOptions:
    data_dir: str
    image_size: (int, int)
    batch_size: int
    saved_model_path: str

    def __init__(self, *, data_dir: str, image_size: (int, int), batch_size: int, saved_model_path: str):
        self.data_dir = data_dir
        self.image_size = image_size
        self.batch_size = batch_size
        self.saved_model_path = saved_model_path


class Trainer:
    options: TrainerOptions

    def __init__(self, options: TrainerOptions):
        self.options = options

    def train(self):
        self.model.fit(
            self.train_generator,
            epochs=5,
            steps_per_epoch=self.train_generator.samples // self.train_generator.batch_size,
            validation_data=self.validation_generator,
            validation_steps=self.validation_generator.samples // self.validation_generator.batch_size)
        tf.saved_model.save(self.model, self.options.saved_model_path)

    @cached_property
    def model(self):
        return model.create(self.train_generator.num_classes)

    @cached_property
    def train_generator(self) -> DirectoryIterator:
        return self.datagen.flow_from_directory(
            self.options.data_dir,
            subset="training",
            shuffle=True,
            interpolation="bilinear",
            target_size=self.options.image_size,
            batch_size=self.options.batch_size)

    @cached_property
    def validation_generator(self) -> DirectoryIterator:
        return self.datagen.flow_from_directory(
            self.options.data_dir,
            subset="validation",
            shuffle=False,
            interpolation="bilinear",
            target_size=self.options.image_size,
            batch_size=self.options.batch_size)

    @cached_property
    def datagen(self) -> tf.keras.preprocessing.image.ImageDataGenerator:
        return tf.keras.preprocessing.image.ImageDataGenerator(
            rescale=1./255,
            validation_split=.20)
