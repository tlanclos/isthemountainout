import tensorflow as tf
import numpy as np
from typing import List, Tuple
from PIL import Image
from enum import Enum


class Classifier:
    model: tf.keras.Model
    labels: List[Enum]

    def __init__(self, *, model: tf.keras.Model, labels: List[Enum]):
        self.model = model
        self.labels = labels

    def classify(self, image: Image) -> Tuple[str, float]:
        img_array = tf.keras.preprocessing.image.img_to_array(image) / 255.0
        img_array = img_array.astype('float32')
        img_array = tf.expand_dims(img_array, 0)  # Create a batch
        score = tf.nn.softmax(self.model(img_array)[0])
        return self.labels[np.argmax(score)], 100 * np.max(score)