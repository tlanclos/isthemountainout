import os
import tensorflow as tf
import common.model as m

from tensorflow.keras.layers import RandomTranslation, RandomBrightness, Cropping2D, Dense, Dropout, GlobalAveragePooling2D, Conv2D, BatchNormalization, MaxPooling2D, SeparableConv2D, Activation, add
from typing import List, Optional
from enum import Enum


class Label(Enum):
    NIGHT = 'Night'
    HIDDEN = 'Hidden'
    MYSTICAL = 'Mystical'
    BEAUTIFUL = 'Beautiful'


def labels() -> List[Label]:
    return sorted(Label.__members__.values(), key=lambda label: label.value)


def generate_model(*, weights_filepath: Optional[str], with_augmentations: bool = False, can_ignore_weights: bool = False):
    shape = (1080, 1920, 3)
    inputs = tf.keras.Input(shape=shape)

    translation_amount = 0.12 if with_augmentations else 0.0
    brightness_amount = 0.10 if with_augmentations else 0.0
    outputs = m.chained(
        # Augmentations
        RandomTranslation(
            translation_amount,
            translation_amount,
            fill_mode='nearest'
        ),
        RandomBrightness(brightness_amount),
        # Cropping2D parameter are how much to take off of top, bottom,
        # left and right, not a rectangle of the cropped image
        Cropping2D(cropping=((160, 350), (580, 450))),
        # Entry Flow
        Conv2D(filters=12, kernel_size=5, strides=2, padding='same'),
        BatchNormalization(),
        Activation('relu'),
        Conv2D(filters=12, kernel_size=5, padding='same'),
        BatchNormalization(),
        Activation('relu'),
        m.expand(
            flow=lambda previous_activation, size: add([
                m.chained(
                    m.duplicate(
                        layers=lambda: [
                            Activation('relu'),
                            SeparableConv2D(
                                filters=size, kernel_size=3, padding='same'),
                            BatchNormalization(),
                        ],
                        count=2
                    ),
                    MaxPooling2D(
                        pool_size=3, strides=2, padding='same'),
                )(previous_activation),
                Conv2D(filters=size, kernel_size=1, strides=2,
                       padding='same')(previous_activation),
            ]),
            values=[32, 16, 8],
        ),

        # Middle Flow
        m.expand(
            flow=lambda previous_activation, _: add([
                m.duplicate(
                    layers=lambda: [
                        Activation('relu'),
                        SeparableConv2D(
                            filters=8, kernel_size=3, padding='same'),
                        BatchNormalization(),
                    ],
                    count=3,
                )(previous_activation),
                previous_activation,
            ]),
            values=[0] * 8
        ),

        # Exit Flow
        lambda previous_activation: add([
            m.chained(
                Activation('relu'),
                SeparableConv2D(
                    filters=728, kernel_size=3, padding='same'),
                BatchNormalization(),
                Activation('relu'),
                SeparableConv2D(
                    filters=1024, kernel_size=3, padding='same'),
                BatchNormalization(),
                MaxPooling2D(pool_size=3, strides=2, padding='same'),
            )(previous_activation),
            Conv2D(filters=1024, kernel_size=1, strides=2,
                   padding='same')(previous_activation),
        ]),
        Activation('relu'),
        SeparableConv2D(filters=728, kernel_size=3, padding='same'),
        BatchNormalization(),
        Activation('relu'),
        SeparableConv2D(filters=1024, kernel_size=3, padding='same'),
        BatchNormalization(),
        GlobalAveragePooling2D(),
        Dense(len(labels()), activation='linear'),
        Dropout(0.2),
    )(inputs)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.build(input_shape=(None, *shape))
    if weights_filepath and os.path.exists(weights_filepath):
        model.load_weights(weights_filepath)
    elif not can_ignore_weights:
        raise Exception(f'No weights found for {weights_filepath}')
    return model
