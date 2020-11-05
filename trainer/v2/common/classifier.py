import tensorflow as tf
import numpy as np
from PIL import Image
from typing import List, Tuple
from enum import Enum


class Classifier:
    model: tf.keras.Model
    labels: List[Enum]

    def __init__(self, *, model: tf.keras.Model, labels: List[Enum]) -> None:
        self.model = model
        self.labels = labels

    def classify(self, image: Image) -> Tuple[str, float]:
        img_array = tf.keras.preprocessing.image.img_to_array(image) / 255.0
        img_array = img_array.astype('float32')
        img_array = tf.expand_dims(img_array, 0)  # Create a batch
        confidences = self.model(img_array)[0]
        score = tf.nn.softmax(confidences)
        index = np.argmax(score)
        return self.labels[index], 100 * confidences[index]
