import tensorflow as tf
import tensorflow_hub as hub

from functools import cached_property

from trainer.common import model
from PIL.Image import Image
from typing import List, Tuple
import numpy as np


class ClassifierOptions:
    saved_model_path: str
    save_labels_file: str

    def __init__(self, *, saved_model_path: str, save_labels_file: str):
        self.saved_model_path = saved_model_path
        self.save_labels_file = save_labels_file


class Classifier:
    options: ClassifierOptions

    def __init__(self, options: ClassifierOptions):
        self.options = options

    def classify(self, filepath: str) -> Tuple[str, float, Image]:
        physical_devices = tf.config.experimental.list_physical_devices('GPU')
        for physical_device in physical_devices:
            tf.config.experimental.set_memory_growth(physical_device, True)

        img = model.image_preprocessor(
            tf.keras.preprocessing.image.load_img(filepath))
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array /= 255.0
        img_array = img_array.astype('float32')
        img_array = tf.expand_dims(img_array, 0)  # Create a batch

        score = tf.nn.softmax(self.model(img_array)[0])
        return self.labels[np.argmax(score)], 100 * np.max(score), img

    @cached_property
    def model(self):
        return tf.keras.models.load_model(self.options.saved_model_path, custom_objects={'KerasLayer': hub.KerasLayer})

    @cached_property
    def labels(self) -> List[str]:
        with open(self.options.save_labels_file, 'r') as f:
            return sorted([label.strip() for label in f.readlines()])
