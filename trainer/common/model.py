import tensorflow as tf
import tensorflow_hub as hub
from PIL import Image


class CroppingOptions:
    x: int
    y: int
    width: int
    height: int

    def __init__(self, *, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


def create(classes: int, *, handle_base: str = 'mobilenet_v2_100_224', pixels: int = 224):
    model = tf.keras.Sequential([
        # Explicitly define the input shape so the model can be properly
        # loaded by the TFLiteConverter
        tf.keras.layers.InputLayer(input_shape=(pixels, pixels, 3)),
        hub.KerasLayer(
            'https://tfhub.dev/google/imagenet/%s/feature_vector/4' % (
                handle_base,),
            trainable=False),
        tf.keras.layers.Dropout(rate=0.2),
        tf.keras.layers.Dense(
            classes, kernel_regularizer=tf.keras.regularizers.l2(0.0001))
    ])
    model.build((None, pixels, pixels, 3))
    model.compile(
        optimizer=tf.keras.optimizers.SGD(lr=0.005, momentum=0.9),
        loss=tf.keras.losses.CategoricalCrossentropy(
            from_logits=True, label_smoothing=0.1),
        metrics=['accuracy'])
    return model


def image_preprocessor(image: Image) -> Image:
    cropping_options = CroppingOptions(x=7868, y=604, width=224, height=224)
    return image.crop((
        cropping_options.x,
        cropping_options.y,
        cropping_options.x + cropping_options.width,
        cropping_options.y + cropping_options.height
    ))
