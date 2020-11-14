import common.model as m
import tensorflow as tf
from enum import Enum
from typing import List

class Label(Enum):
    NIGHT = 'Night'
    NOT_VISIBLE = 'NotVisible'
    MYSTICAL = 'Mystical'
    BEAUTIFUL = 'Beautiful'


def generate() -> tf.keras.Model:
    shape = (224, 224, 3)
    inputs = tf.keras.Input(shape=shape)
    outputs = m.chained(
        # Entry Flow
        tf.keras.layers.Conv2D(filters=32, kernel_size=3, strides=2, padding='same'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Activation('relu'),
        tf.keras.layers.Conv2D(filters=64, kernel_size=3, padding='same'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Activation('relu'),
        m.expand(
            flow=lambda previous_activation, size: tf.keras.layers.add([
                m.chained(
                    m.duplicate(
                        layers=lambda: [
                            tf.keras.layers.Activation('relu'),
                            tf.keras.layers.SeparableConv2D(filters=size, kernel_size=3, padding='same'),
                            tf.keras.layers.BatchNormalization(),
                        ],
                        count=2
                    ),
                    tf.keras.layers.MaxPooling2D(pool_size=3, strides=2, padding='same'),
                )(previous_activation),
                tf.keras.layers.Conv2D(filters=size, kernel_size=1, strides=2, padding='same')(previous_activation),
            ]),
            values=[128, 256, 728],
        ),

        # # Middle Flow
        m.expand(
            flow=lambda previous_activation, _: tf.keras.layers.add([
                m.duplicate(
                    layers=lambda: [
                        tf.keras.layers.Activation('relu'),
                        tf.keras.layers.SeparableConv2D(filters=728, kernel_size=3, padding='same'),
                        tf.keras.layers.BatchNormalization(),
                    ],
                    count=3,
                )(previous_activation),
                previous_activation,
            ]),
            values=[0] * 8
        ),

        # # Exit Flow
        lambda previous_activation: tf.keras.layers.add([
            m.chained(
                tf.keras.layers.Activation('relu'),
                tf.keras.layers.SeparableConv2D(filters=728, kernel_size=3, padding='same'),
                tf.keras.layers.BatchNormalization(),
                tf.keras.layers.Activation('relu'),
                tf.keras.layers.SeparableConv2D(filters=1024, kernel_size=3, padding='same'),
                tf.keras.layers.BatchNormalization(),
                tf.keras.layers.MaxPooling2D(pool_size=3, strides=2, padding='same'),
            )(previous_activation),
            tf.keras.layers.Conv2D(filters=1024, kernel_size=1, strides=2, padding='same')(previous_activation),
        ]),
        tf.keras.layers.Activation('relu'),
        tf.keras.layers.SeparableConv2D(filters=728, kernel_size=3, padding='same'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Activation('relu'),
        tf.keras.layers.SeparableConv2D(filters=1024, kernel_size=3, padding='same'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(len(labels()), activation='linear'),
        tf.keras.layers.Dropout(0.2),
    )(inputs)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.build(input_shape=(None, *shape))
    model.load_weights('isthemountainout.h5')
    return model


def labels() -> List[Label]:
    return sorted(Label.__members__.values(), key=lambda label: label.value)
