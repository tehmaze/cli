import sys
import termios
import tty

def singleton(cls):
    instance_container = []
    def getinstance():
        if not len(instance_container):
            instance_container.append(cls())
        return instance_container[0]
    return getinstance


@singleton
class Console(object):
    '''
    Socket-like object that uses stdin/stdout for reading/writing.
    '''

    def __init__(self):
        self._buffered = True
        self.debuffer()

    def __delete__(self):
        self.restore()

    def debuffer(self):
        if self._buffered:
            self._fd = self.fileno()
            self.old = termios.tcgetattr(self._fd)
            tty.setraw(self._fd)
            self._buffered = not self._buffered

    def restore(self):
        if not self._buffered:
            tty.setcbreak(self._fd)
            tcsetattr_flags = termios.TCSAFLUSH
            if hasattr(termios, 'TCSASOFT'):
                tcsetattr_flags |= termios.TCSASOFT
            termios.tcsetattr(self._fd, tcsetattr_flags, self.old)
            self.send('\x1b[0m')   # reset graphic rendition
            self._buffered = not self._buffered

    def getsockname(self):
        return ('0.0.0.0', 0)

    def fileno(self):
        return sys.stdin.fileno()

    def flush(self):
        return sys.stdout.flush()

    def send(self, string, flags=0):
        return sys.stdout.write(string)

    def recv(self, bufsize=4096, flags=0):
        return sys.stdin.read(bufsize)
