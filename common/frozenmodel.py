from enum import Enum
from typing import List

try:
    import tensorflow as tf
    Interpreter = tf.lite.Interpreter
except:
    from tflite_runtime.interpreter import Interpreter


class Label(Enum):
    NIGHT = 'Night'
    HIDDEN = 'Hidden'
    MYSTICAL = 'Mystical'
    BEAUTIFUL = 'Beautiful'


def labels() -> List[Label]:
    return sorted(Label.__members__.values(), key=lambda label: label.value)


def load_saved_model(*, model_filepath: str) -> Interpreter:
    return Interpreter(model_path=model_filepath)
