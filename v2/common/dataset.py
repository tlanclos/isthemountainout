import tensorflow as tf


class Dataset:
    original: tf.data.Dataset
    training: tf.data.Dataset
    validation: tf.data.Dataset
    test: tf.data.Dataset

    def __init__(self, dataset: tf.data.Dataset, *, splits=(0.8, 0.1, 0.1)):
        (training_split, validation_split, test_split) = splits
        assert (training_split + validation_split + test_split) == 1

        dataset_size = tf.data.experimental.cardinality(dataset).numpy()
        training_size = int(dataset_size * training_split)
        validation_size = int(dataset_size * validation_split)

        self.original = dataset
        self.training = dataset.take(training_size)
        self.validation = dataset.skip(training_size).take(validation_size)
        self.test = dataset.skip(training_size).skip(validation_size)
