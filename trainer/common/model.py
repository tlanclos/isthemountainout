import os
import io
import tensorflow as tf
import numpy as np
import itertools
import sklearn.metrics
from datetime import datetime
from matplotlib import pyplot as plt
from functools import reduce


def chained(*layers):
    assert len(layers) >= 1, 'chainned layers must have at least 1 layer'
    def __chained(input):
        return reduce(lambda acc, curr: curr(acc), layers, input)
    return __chained


def merge(*layers, merger):
    return merger(list(layers))


def duplicate(*, layers, count):
    return chained(*[layer for layer in itertools.chain(*[layers() for _ in range(count)])])


def expand(*, flow, values):
    def __expand(input):
        previous_activation = input
        for value in values:
            previous_activation = flow(previous_activation, value)
        return previous_activation
    return __expand


class LogConfusionMatrixCallback(tf.keras.callbacks.Callback):
    def __init__(self, *, model, datagen, logdir):
        super().__init__()
        self.model = model
        self.datagen = datagen
        self.class_names = list(datagen.class_indices.keys())
        self.logdir = logdir

    def on_epoch_end(self, epoch, logs=None):
        # Use the model to predict the values from the validation dataset.
        data, labels = self.datagen.next()
        test_pred_raw = self.model.predict(data)
        test_pred = np.argmax(test_pred_raw, axis=1)
        test_label = np.argmax(labels, axis=1)

        # Calculate the confusion matrix.
        cm = sklearn.metrics.confusion_matrix(test_label, test_pred)
        # Log the confusion matrix as an image summary.
        figure = self.plot_confusion_matrix(cm, class_names=self.class_names)
        cm_image = self.plot_to_image(figure)

        # Log the confusion matrix as an image summary.
        file_writer = tf.summary.create_file_writer(
            os.path.join(self.logdir, datetime.now().strftime('%Y%m%d-%H%M%S'), 'cm'))
        with file_writer.as_default():
            tf.summary.image('Confusion Matrix', cm_image, step=epoch)

    def plot_confusion_matrix(self, cm, *, class_names):
        """
        Returns a matplotlib figure containing the plotted confusion matrix.

        Args:
            cm (array, shape = [n, n]): a confusion matrix of integer classes
            class_names (array, shape = [n]): String names of the integer classes
        """
        figure = plt.figure(figsize=(8, 8))
        plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        plt.title("Confusion matrix")
        plt.colorbar()
        tick_marks = np.arange(len(class_names))
        plt.xticks(tick_marks, class_names, rotation=45)
        plt.yticks(tick_marks, class_names)

        # Normalize the confusion matrix.
        cm = np.around(cm.astype('float') / cm.sum(axis=1)[:, np.newaxis], decimals=2)

        # Use white text if squares are dark; otherwise black.
        threshold = cm.max() / 2.
        for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
            color = "white" if cm[i, j] > threshold else "black"
            plt.text(j, i, cm[i, j], horizontalalignment="center", color=color)

        plt.tight_layout()
        plt.subplots_adjust(left=0.125, right=0.9, bottom=0.1, top=0.9, wspace=0.2, hspace=0.2)
        plt.ylabel('True label')
        plt.xlabel('Predicted label')
        return figure

    def plot_to_image(self, figure):
        """Converts the matplotlib plot specified by 'figure' to a PNG image and
        returns it. The supplied figure is closed and inaccessible after this call."""
        # Save the plot to a PNG in memory.
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        # Closing the figure prevents it from being displayed directly inside
        # the notebook.
        plt.close(figure)
        buf.seek(0)
        # Convert PNG buffer to TF image
        image = tf.image.decode_png(buf.getvalue(), channels=4)
        # Add the batch dimension
        image = tf.expand_dims(image, 0)
        return image