#! /usr/bin/python -u

import re
import sys
import textwrap
from cli.console import Console
from cli.section import Root
from cli.history import History
from cli.parser import parse, TokenPipe
from cli.sink import Sink
from cli.filter import Filter

MODE_INPUT, MODE_REVERSE_SEARCH, MODE_FORWARD_SEARCH = range(3)
RE_NEWLINE = re.compile(r'(?:\r\n|\n)')

class Interface(object):
    re_arg = re.compile(r'^do_(?P<func>\S+)\(\) takes exactly (?P<args>\d+) arguments')
    sequence = {
        '\x1b\x5b\x41':         'up',
        '\x1b\x5b\x42':         'down',
        '\x1b\x5b\x43':         'right',
        '\x1b\x5b\x44':         'left',
        '\x1b\x5b\x35':         'pgup',
        '\x1b\x5b\x36':         'pgdn',

        '\x1b\x4f\x50':         'F1',
        '\x1b\x4f\x51':         'F2',
        '\x1b\x4f\x52':         'F3',
        '\x1b\x4f\x53':         'F4',
        '\x1b\x5b\x31\x35\x7e': 'F5',
        '\x1b\x5b\x31\x37\x7e': 'F6',
        '\x1b\x5b\x31\x38\x7e': 'F7',
        '\x1b\x5b\x31\x39\x7e': 'F8',
        '\x1b\x5b\x32\x30\x7e': 'F9',
        '\x1b\x5b\x32\x31\x7e': 'F10',
        '\x1b\x5b\x32\x33\x7e': 'F11',
        '\x1b\x5b\x32\x34\x7e': 'F12',

        '\x1b\x5b\x32\x7e':     'ins',
        '\x1b\x5b\x33\x7e':     'del',
        '\x1b\x4f\x46':         'end',
        '\x1b\x4f\x48':         'home',
        '\x1b\x1b':             'esc',
        '\x09':                 'tab',
        '\x0a':                 'enter',
        '\x20':                 'space',
        '\x7f':                 'backspace'
    }

    alias = {
        '?': 'help',
    }

    root_class = Root
    filter_class = Filter
    history_class = History

    def __init__(self, socket=None, name='cli', prompt='%(name)s %(path)s%% '):
        self.socket = socket or Console()
        self.name = name
        self.prompt_default = prompt
        self.prompt_alternate = None
        self.buffer = ''
        self.linepos = 0
        self.mode = MODE_INPUT
        self.char = self.last = chr(0)
        self.history = self.history_class()
        self.histpos = -1
        self.root = self.root_class(self)
        self.filter = self.filter_class(self)
        self.section = self.root
        self.errors = []
        self.is_running = True
        self.send(self.prompt)

    @property
    def prompt(self):
        if self.prompt_alternate:
            return self.prompt_alternate
        else:
            path = '-'.join(self.section.path)
            return self.prompt_default % dict(
                name = self.name,
                path = path,
            )

    def send(self, data):
        # make sure we send correct newlines (including carriage return)
        data = '\r\n'.join(RE_NEWLINE.split(data))
        self.socket.send(data)
        self.socket.flush()

    def sendline(self, data=''):
        self.send(data + '\r\n')
        self.send(self.prompt)

    def fileno(self):
        return self.socket.fileno()

    def read(self):
        self.last = self.char
        self.char = self.socket.recv(1)

        # ^C / ^D
        if self.char in ['\x03', '\x04']:
            if self.buffer:
                if self.section != self.root:
                    self.section = self.section.parent
                self.buffer = ''
                self.send('\x07')
                self.sendline('')
                self.history.reset()
            else:
                sink = Sink()
                self.root.exit(sink)
                self.send(sink.output)
                sys.exit(0)

        # ^Z
        elif self.char == '\x1a':
            if self.section != self.root:
                self.section = self.section.parent
                self.buffer = ''
                self.sendline('')
            else:
                sink = Sink()
                self.root.exit(sink)
                self.send(sink.output)
                sys.exit(0)

        # ^H / backspace
        elif self.char == '\x08':
            if self.mode == MODE_INPUT:
                buffer = ''.join([
                    self.buffer[:max(0, self.linepos - 1)],
                    self.buffer[self.linepos:]
                ])
                self.buffer_update(buffer, self.linepos - 1)

            elif self.mode == MODE_REVERSE_SEARCH:
                filter = self.buffer[:-1]
                self.handle_search(self.char, filter, self.history[::-1])

            elif self.mode == MODE_FORWARD_SEARCH:
                filter = self.buffer[:-1]
                self.handle_search(self.char, filter, self.history)

        # ^I / tab
        elif self.char == '\x09':
            tabs = self.section.complete(self.buffer)
            if len(tabs) == 0:
                self.send('\x07') # beep
            elif len(tabs) == 1:
                self.buffer_update(tabs[0] + ' ')
            else:
                # remove everything upto the last completed item so that
                # completing the items won't clutter your display
                if ' ' in self.buffer:
                    repl = ' '.join(self.buffer.split(' ')[:-1])
                    tabs = [tab.replace(repl, '').lstrip() for tab in tabs]
                tabs.sort()
                self.sendline('\n\r%s' % (' '.join(tabs),))
                self.buffer_update(self.buffer)

        # ?
        elif self.char == '?':
            tabs = self.section.complete(self.buffer, include_root=False)
            if len(tabs) == 0:
                self.sendline('\x07')
            elif len(tabs) == 1:
                tabs = self.section.complete(tabs[0] + ' ', include_root=False)
                tabs.sort()
                self.send('\r\n')
                pads = ' ' * len(self.prompt)
                for item in tabs:
                    self.send(''.join([pads, item, '\r\n']))
                self.buffer_update(self.buffer)
            else:
                tabs.sort()
                self.send('\r\n')
                pads = ' ' * len(self.prompt)
                size = max(map(len, tabs))
                fmts = '%%s%%-%ds %%s\r\n' % (size,)
                for item in tabs:
                    #self.send(''.join([pads, item, '\r\n']))
                    docs = self.root._get_syntax(item)
                    self.send(fmts % (pads, item, docs))
                self.buffer_update(self.buffer)

        # escape
        elif self.char in ('\x1b', '\x1b\x4f', '\x1b\x5b'):
            # read complete escape sequence
            while self.char in ('\x1b', '\x1b\x4f', '\x1b\x5b') or \
                self.char[:3] in ('\x1b\x5b\x31', '\x1b\x5b\x32', '\x1b\x5b\x33'):
                self.char += self.socket.recv(1)
                if self.char[-1] == '\x7e':
                    break
            self.handle_special(self.char)

        # ^R / reverse-search
        elif self.char == '\x12':
            self.mode = MODE_REVERSE_SEARCH
            self.prompt_alternate = '(reverse-search): '
            self.buffer_update('')

        # ^S / forward-search
        elif self.char == '\x13':
            self.mode = MODE_FORWARD_SEARCH
            self.prompt_alternate = '(forward-search): '
            self.buffer_update('')

        # ^W / erase-word
        elif self.char == '\x17':
            if self.linepos == 0:
                self.buffer_update(self.buffer)
                return

            marker = None
            buffer = self.buffer[:self.linepos].rstrip(' \t')
            for pos, char in list(enumerate(buffer))[::-1]:
                if pos == 0:
                    marker = 0
                    break

                elif char in ' \t':
                    marker = pos + 1
                    break

            if marker is not None:
                buffer = ''.join([
                    self.buffer[:marker],
                    self.buffer[self.linepos:]
                ])
                self.buffer_update(buffer, marker)
            else:
                self.buffer_update(self.buffer, self.linepos)

        # regular self.characters
        elif self.char >= '\x20' and self.char < '\x7f':
            if self.mode == MODE_INPUT:
                #self.buffer += self.char
                #self.send(self.char)
                buffer = ''.join([
                    self.buffer[:self.linepos],
                    self.char,
                    self.buffer[self.linepos:]
                ])
                self.buffer_update(buffer, self.linepos + 1)

            elif self.mode == MODE_REVERSE_SEARCH:
                filter = self.buffer + self.char
                self.handle_search(self.char, filter, self.history[::-1])

            elif self.mode == MODE_FORWARD_SEARCH:
                filter = self.buffer + self.char
                self.handle_search(self.char, filter, self.history)

        # ^L / redraw
        elif self.char == '\x0c':
            self.sendline('')
            self.buffer_update(self.buffer)

        # ^M / enter
        elif self.char in ['\x0a', '\x0d']:
            self.prompt_alternate = None
            if self.mode == MODE_INPUT:
                self.send('\r\n')
                self.handle_command(self.buffer.strip())
            else:
                self.mode = MODE_INPUT
                self.sendline('')
                self.buffer_update(self.search)

        # fallback
        else:
            self.sendline('chr(0x%02x)' % (ord(self.char),))

    def buffer_update(self, new_buffer, linepos=None):
        self.send('\r%s%s' % (self.prompt, ' ' * len(self.buffer)))
        self.buffer = new_buffer
        self.send('\r%s%s' % (self.prompt, self.buffer))
        if linepos is None:
            self.linepos = len(self.buffer)
        else:
            # normalise
            linepos = max(0, min(len(self.buffer), linepos))
            self.send('\b' * (max(0, len(self.buffer) - linepos)))
            self.linepos = linepos

    def handle_search(self, char, filter, history):
        self.search = ''
        for item in history:
            if filter in item:
                self.search = item
                break

        if self.search:
            self.buffer_update(self.search)
            self.buffer = filter
            self.send('\b' * (len(self.search) - self.search.index(filter)))
        else:
            self.send('\x07') # beep

    def handle_command(self, line):
        self.buffer = ''
        if not line.strip():
            self.mode = MODE_INPUT
            self.sendline('')
            return

        if line:
            sink = Sink()

            # parse user input, split into pipe chunks
            pipe = []
            part = []
            for token in parse(line):
                if isinstance(token, TokenPipe):
                    pipe.append(' '.join(part))
                    part = []
                else:
                    part.append(str(token))
            if part:
                pipe.append(' '.join(part))

            # evaluate pipe
            try:
                for i, part in enumerate(pipe):
                    # first pipe entry is a command
                    if i == 0:
                        if not self.section.execute(sink, part):
                            break
                    # all that follow are a filter
                    else:
                        if not self.filter.execute(sink, part):
                            break
                self.send(sink.output)
                self.history.append(line)
                self.history.reset()
                self.buffer_update('')
                return
            except Exception, e:
                raise
                error = str(e)
                test = self.re_arg.match(error)
                if test:
                    func = test.groupdict()['func']
                    args = int(test.groupdict()['args']) - 1
                    error = '%s takes %d arguments' % (func, args)
                    self.send('error: %s\n' % (error,))
                    self.do_help(func, single=True)
                    self.sendline('')
                else:
                    self.sendline('error: %s' % (error,))
                return

            if line.startswith('!'):
                if line.split()[0][1:].isdigit():
                    back = int(line.split()[0][1:])
                    if back >= len(self.history):
                        self.sendline('event not found')
                    else:
                        self.handle_command(self.history[back])
                    return

                else:
                    back = line.split()[0][1:]
                    for item in self.history[::-1]:
                        if item.startswith(back):
                            return self.handle_command(item)
                    self.sendline('event not found')
                    return

        self.sendline('what? you need "help"')

    def handle_special(self, sequence):
        #print 'special', repr(line), '\r\n'

        if sequence in self.sequence:
            key = self.sequence[sequence]

            # esc
            if key == 'esc':
                self.mode = MODE_INPUT
                self.prompt_alternate = None
                self.buffer_update('')
                self.history.reset()

            # up
            elif key == 'up':
                if self.history:
                    self.buffer_update(self.history.backward())

            # left
            elif key == 'left':
                self.buffer_update(self.buffer, self.linepos - 1)

            # right
            elif key == 'right':
                self.buffer_update(self.buffer, self.linepos + 1)

            # down
            elif key == 'down':
                if self.history:
                    if (self.history.position + 1) == len(self.history):
                        self.buffer_update('')
                    else:
                        self.buffer_update(self.history.forward())


if __name__ == '__main__':
    import select
    from section import Section, command

    class Test(Section):
        name = 'test'

        @command
        def ping(self, sink):
            self.interface.sendline('pong!')

        @command
        def version(self, sink):
            self.interface.sendline('Python %s' % (sys.version,))

    class Bogus(Section):
        name = 'bogus'

        @command
        def error(self, sink):
            raise Exception('bogus')

    con = Console()
    try:
        cli = Interface(socket=con)
        cli.root.addchild(Test())
        cli.root.addchild(Bogus())
        while cli.is_running:
            r, w, e = select.select([cli], [], [], 0.1)
            if r:
                cli.read()
    finally:
        con.restore()


