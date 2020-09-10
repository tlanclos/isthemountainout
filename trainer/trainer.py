from functools import cached_property
from matplotlib import pyplot as plt

import tensorflow as tf
import tensorflow_hub as hub
from tensorflow.python.keras.preprocessing.image import DirectoryIterator

from trainer.common import model


class TrainerOptions:
    data_dir: str
    image_size: (int, int)
    batch_size: int
    saved_model_path: str
    visualize: bool
    allow_memory_growth: bool

    def __init__(self, *, data_dir: str, image_size: (int, int), batch_size: int, saved_model_path: str, visualize: bool, allow_memory_growth: bool):
        self.data_dir = data_dir
        self.image_size = image_size
        self.batch_size = batch_size
        self.saved_model_path = saved_model_path
        self.visualize = visualize
        self.allow_memory_growth = allow_memory_growth


class Trainer:
    options: TrainerOptions

    def __init__(self, options: TrainerOptions):
        self.options = options
        if self.options.allow_memory_growth:
            for device in tf.config.experimental.list_physical_devices('GPU'):
                tf.config.experimental.set_memory_growth(device, True)

    def train(self):
        fit = self.model.fit(
            self.train_generator,
            epochs=5,
            steps_per_epoch=self.train_generator.samples // self.train_generator.batch_size,
            validation_data=self.validation_generator,
            validation_steps=self.validation_generator.samples // self.validation_generator.batch_size)
        self.__visualize(fit.history)
        self.model.save(self.options.saved_model_path, save_format='h5')

    def __visualize(self, hist):
        if self.options.visualize:
            plt.figure()
            plt.ylabel("Loss (training and validation)")
            plt.xlabel("Training Steps")
            plt.ylim([0, 2])
            plt.plot(hist["loss"])

            plt.figure()
            plt.ylabel("Accuracy (training and validation)")
            plt.xlabel("Training Steps")
            plt.ylim([0, 1])
            plt.plot(hist["accuracy"])
            plt.show()

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
