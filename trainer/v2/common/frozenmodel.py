import common.model as m
import tensorflow as tf


def generate(classes: int) -> tf.keras.Model:
    shape = (224, 224, 3)
    inputs = tf.keras.Input(shape=shape)
    outputs = m.chained(
        tf.keras.layers.add([
            m.chained(
                inputs,
                tf.keras.layers.Lambda(
                    lambda image: tf.image.rgb_to_grayscale(image)),
                tf.keras.layers.Conv2D(
                    filters=64, kernel_size=3, activation='relu'),
                tf.keras.layers.MaxPooling2D(2),
                tf.keras.layers.Conv2D(
                    filters=64, kernel_size=3, activation='relu'),
                tf.keras.layers.MaxPooling2D(2),
                tf.keras.layers.Dropout(0.1),
                tf.keras.layers.Conv2D(
                    filters=64, kernel_size=3, activation='relu'),
                tf.keras.layers.MaxPooling2D(2),
                tf.keras.layers.Flatten(),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(32),
            ),
            m.chained(
                inputs,
                tf.keras.layers.Lambda(
                    lambda image: tf.image.rgb_to_grayscale(image)),
                tf.keras.layers.Conv2DTranspose(
                    filters=64, kernel_size=3, activation='relu'),
                tf.keras.layers.MaxPooling2D(2),
                tf.keras.layers.Conv2DTranspose(
                    filters=64, kernel_size=3, activation='relu'),
                tf.keras.layers.MaxPooling2D(2),
                tf.keras.layers.Dropout(0.1),
                tf.keras.layers.Conv2DTranspose(
                    filters=64, kernel_size=3, activation='relu'),
                tf.keras.layers.MaxPooling2D(2),
                tf.keras.layers.Flatten(),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(32),
            ),
        ]),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(classes),
        tf.keras.layers.Activation('softmax'))
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.build(input_shape=(None, *shape))
    model.load_weights('isthemountainout.h5')
    return model
