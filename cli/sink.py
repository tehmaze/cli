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


class FileLike(list):
    '''
    Allow file-like calls on this buffer.
    '''

    def __init__(self, data=None):
        if data:
            self.write(data)

        def na(self,*args):
            raise NotImplementedError('Not available')
        for fake in ['fd', 'name', 'seek']:
            setattr(self, fake, na)

    def __call__(self, data):
        self.write(data)
        return self

    def __str__(self):
        return self.getvalue()

    def __unicode__(self):
        return self.getvalue()

    def tell(self):
        return len(self.getvalue())

    def flush(self):
        for x in xrange(0, len(self)):
            self.pop(0)

    def write(self, data):
        self.append((time.time(), data))
        return self

    def getvalue(self):
        return ''.join((chunk[1] for chunk in self))


class Sink(object):
    '''
    Output sink that collects data.
    '''

    def __init__(self, out=None, err=None):
        self.buffers = dict(
            stdout = FileLike(),
            stderr = FileLike(),
        )

    def __iter__(self):
        for chunk in sorted(reduce(add, self.buffers.values())):
            yield chunk[1]

    def stdout_get(self):
        return self.buffers['stdout']

    def stdout_set(self, data):
        self.stdout.flush()
        self.stdout.write(data)

    def stderr_get(self):
        return self.buffers['stderr']

    def stderr_set(self, data):
        self.stderr.flush()
        self.stderr.write(data)

    stdout = property(stdout_get, stdout_set)
    stderr = property(stderr_get, stderr_set)

    @property
    def output(self):
        return ''.join(list(iter(self)))

    def flush(self):
        for item in self.buffers:
            self.buffers[item].flush()

    reset = flush

    def write(self, data):
        self.buffers['stdout'].write(data)

    def error(self, data):
        self.buffers['stderr'].write(data)
