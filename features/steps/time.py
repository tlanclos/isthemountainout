from behave import *
from datetime import datetime


@given('today is {value:ti}')
def provide_time(context, value: datetime):
    context.today = value
