try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
try:
    reduce(lambda a: a, [None])
except NameError:
    from functools import reduce
from operator import add
import time


class Sink(object):
    '''
    Output sink that collects data.
    '''

    def __init__(self, out=None, err=None):
        self.buffers = dict(
            stdout = [],
            stderr = [],
        )

    def __iter__(self):
        for chunk in sorted(reduce(add, self.buffers.values())):
            yield chunk[1]

    @property
    def stdout(self):
        return ''.join([chunk[1] for chunk in self.buffers['stdout']])

    @property
    def stderr(self):
        return ''.join([chunk[1] for chunk in self.buffers['stderr']])

    @property
    def output(self):
        return ''.join(list(iter(self)))

    def reset(self):
        for item in self.buffers:
            self.buffers[item] = []

    def write(self, data):
        self.buffers['stdout'].append((time.time(), data))

    def error(self, data):
        self.buffers['stderr'].append((time.time(), data))
