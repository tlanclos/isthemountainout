import itertools
import os

import matplotlib.pylab as plt
import numpy as np

import tensorflow as tf
import tensorflow_hub as hub

print("TF version", tf.__version__)
print("Hub version:", hub.__version__)
print("GPU is", 'available' if len(
    tf.config.list_physical_devices('GPU')) > 0 else 'NOT AVAILABLE')

module_selection = ("mobilenet_v2_100_224", 224)
handle_base, pixels = module_selection
MODULE_HANDLE = "https://tfhub.dev/google/imagenet/%s/feature_vector/4" % (
    handle_base,)
IMAGE_SIZE = (pixels, pixels)
print("Using %s with input size %s" % (MODULE_HANDLE, IMAGE_SIZE))

BATCH_SIZE = 32
