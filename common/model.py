import itertools
from functools import reduce


def chained(*layers):
    assert len(layers) >= 1, 'chainned layers must have at least 1 layer'

    def __chained(input):
        return reduce(lambda acc, curr: curr(acc), layers, input)
    return __chained


def merge(*layers, merger):
    return merger(list(layers))


def duplicate(*, layers, count):
    return chained(*[
        layer for layer in itertools.chain(*[
            layers() for _ in range(count)])])


def expand(*, flow, values):
    def __expand(input):
        previous_activation = input
        for value in values:
            previous_activation = flow(previous_activation, value)
        return previous_activation
    return __expand
