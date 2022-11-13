import tensorflow as tf
import common.model as m

from tensorflow.keras import layers
from typing import List
from enum import Enum


class Label(Enum):
    NIGHT = 'Night'
    NOT_VISIBLE = 'NotVisible'
    MYSTICAL = 'Mystical'
    BEAUTIFUL = 'Beautiful'


def labels() -> List[Label]:
    return sorted(Label.__members__.values(), key=lambda label: label.value)


def generate_model(*, weights_filepath: str):
    shape = (1080, 1920, 3)
    inputs = tf.keras.Input(shape=shape)
    outputs = m.chained(
        # Augmentations
        layers.RandomTranslation(
            0.0,
            0.0,
            fill_mode='nearest'
        ),
        layers.RandomBrightness(0.0),
        # Cropping2D parameter are how much to take off of top, bottom,
        # left and right, not a rectangle of the cropped image
        layers.Cropping2D(cropping=((160, 350), (580, 450))),
        # Entry Flow
        layers.Conv2D(filters=32, kernel_size=3, strides=2, padding='same'),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.Conv2D(filters=64, kernel_size=3, padding='same'),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        m.expand(
            flow=lambda previous_activation, size: layers.add([
                m.chained(
                    m.duplicate(
                        layers=lambda: [
                            layers.Activation('relu'),
                            layers.SeparableConv2D(
                                filters=size, kernel_size=3, padding='same'),
                            layers.BatchNormalization(),
                        ],
                        count=2
                    ),
                    layers.MaxPooling2D(
                        pool_size=3, strides=2, padding='same'),
                )(previous_activation),
                layers.Conv2D(filters=size, kernel_size=1, strides=2,
                              padding='same')(previous_activation),
            ]),
            values=[128, 256, 728],
        ),

        # Middle Flow
        m.expand(
            flow=lambda previous_activation, _: layers.add([
                m.duplicate(
                    layers=lambda: [
                        layers.Activation('relu'),
                        layers.SeparableConv2D(
                            filters=728, kernel_size=3, padding='same'),
                        layers.BatchNormalization(),
                    ],
                    count=3,
                )(previous_activation),
                previous_activation,
            ]),
            values=[0] * 8
        ),

        # Exit Flow
        lambda previous_activation: layers.add([
            m.chained(
                layers.Activation('relu'),
                layers.SeparableConv2D(
                    filters=728, kernel_size=3, padding='same'),
                layers.BatchNormalization(),
                layers.Activation('relu'),
                layers.SeparableConv2D(
                    filters=1024, kernel_size=3, padding='same'),
                layers.BatchNormalization(),
                layers.MaxPooling2D(pool_size=3, strides=2, padding='same'),
            )(previous_activation),
            layers.Conv2D(filters=1024, kernel_size=1, strides=2,
                          padding='same')(previous_activation),
        ]),
        layers.Activation('relu'),
        layers.SeparableConv2D(filters=728, kernel_size=3, padding='same'),
        layers.BatchNormalization(),
        layers.Activation('relu'),
        layers.SeparableConv2D(filters=1024, kernel_size=3, padding='same'),
        layers.BatchNormalization(),
        layers.GlobalAveragePooling2D(),
        layers.Dense(len(labels()), activation='linear'),
        layers.Dropout(0.2),
    )(inputs)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.build(input_shape=(None, *shape))
    model.load_weights(weights_filepath)
    return model
