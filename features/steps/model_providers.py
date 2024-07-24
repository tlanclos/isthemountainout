import os
from behave import *

from common.frozenmodel import load_saved_model


FILEPATH = os.path.dirname(__file__)


@given('the isthemountainout model interpreter')
def provide_isthemountainout_model(context):
    context.interpreter = load_saved_model(
        model_filepath=os.path.join(f'{FILEPATH}/../../resources/model.tflite'))
