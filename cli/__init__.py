#! /usr/bin/python -u

import re
import sys
import textwrap
from console import Console

MODE_INPUT, MODE_REVERSE_SEARCH, MODE_FORWARD_SEARCH = range(3)


class CLI(object):
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

    def __init__(self, socket=None, prompt='cli% '):
        self.socket = socket or Console()
        self.prompt = self.prompt_default = prompt
        self.buffer = ''
        self.history = []
        self.histpos = -1
        self.mode = MODE_INPUT
        self.char = self.last = chr(0)
        self.send(self.prompt)

    def send(self, data):
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

        # ^C / ^D / ^Z
        if self.char in ['\x03', '\x04', '\x1a']:
            if self.buffer:
                self.buffer = ''
                self.send('\x07')
                self.sendline('')
                self.histpos = len(self.history)
            else:
                self.do_exit()

        # ^H / backspace
        elif self.char == '\x08':
            if self.mode == MODE_INPUT:
                self.buffer_update(self.buffer[:-1])

            elif self.mode == MODE_REVERSE_SEARCH:
                filter = self.buffer[:-1]
                self.handle_search(self.char, filter, self.history[::-1])

            elif self.mode == MODE_FORWARD_SEARCH:
                filter = self.buffer[:-1]
                self.handle_search(self.char, filter, self.history)

        # ^I / tab
        elif self.char == '\x09':
            tabs = [x.replace('do_', '') for x in dir(self) if x.startswith('do_%s' % (self.buffer,))]
            if len(tabs) == 0:
                self.send('\x07') # beep
            elif len(tabs) == 1:
                self.buffer = tabs[0] + ' '
                self.send('\r%s%s' % (self.prompt, self.buffer))
            else:
                tabs.sort()
                self.sendline('\n\r%s' % (' '.join(tabs),))
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
            self.prompt = '(reverse-search): '
            self.buffer_update('')

        # ^S / forward-search
        elif self.char == '\x13':
            self.mode = MODE_FORWARD_SEARCH
            self.prompt = '(forward-search): '
            self.buffer_update('')

        # ^W / wipe-word
        elif self.char == '\x17':
            self.buffer_update(' '.join(self.buffer.split(' ')[:-1]))

        # regular self.characters
        elif self.char >= '\x20' and self.char <= '\x7a':
            if self.mode == MODE_INPUT:
                self.buffer += self.char
                self.send(self.char)

            elif self.mode == MODE_REVERSE_SEARCH:
                filter = self.buffer + self.char
                self.handle_search(self.char, filter, self.history[::-1])

            elif self.mode == MODE_FORWARD_SEARCH:
                filter = self.buffer + self.char
                self.handle_search(self.char, filter, self.history)

        # ^M / enter
        elif self.char in ['\x0a', '\x0d']:
            self.prompt = self.prompt_default
            if self.mode == MODE_INPUT:
                self.send('\r\n')
                self.handle_command(self.buffer.strip())
            else:
                self.mode = MODE_INPUT
                self.sendline('')
                self.buffer_update(self.search)

        # fallback
        else:
            self.sendline('')

    def buffer_update(self, new_buffer):
        self.send('\r%s%s' % (self.prompt, ' ' * len(self.buffer)))
        self.buffer = new_buffer
        self.send('\r%s%s' % (self.prompt, self.buffer))

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

        if ' ' in line:
            cmnd, args = line.strip().split(' ', 1)
        else:
            cmnd = line.strip()
            args = ''

        if cmnd:
            cmnd = self.alias.get(cmnd, cmnd)
            hook = getattr(self, 'do_%s' % (cmnd,), None)
            if hook:
                try:
                    self.history.append(line)
                    self.histpos = len(self.history)
                    return hook(*args.split())
                except Exception, e:
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

            elif cmnd.startswith('!'):
                if cmnd.split()[0][1:].isdigit():
                    back = int(cmnd.split()[0][1:])
                    if back >= len(self.history):
                        self.sendline('event not found')
                    else:
                        self.handle_command(self.history[back])
                    return

                else:
                    back = cmnd.split()[0][1:]
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
                self.prompt = self.prompt_default
                self.buffer_update('')
                self.histpos = len(self.history)

            # up
            elif key == 'up':
                if self.history:
                    self.histpos = max(self.histpos - 1, 0)
                    self.buffer_update(self.history[self.histpos])

            # down
            elif key == 'down':
                if self.history:
                    self.histpos = min(self.histpos + 1, len(self.history))
                    if self.histpos == len(self.history):
                        self.buffer_update('')
                    else:
                        self.buffer_update(self.history[self.histpos])


    def do_help(self, *args, **kwargs):
        '''
        syntax:  help [<command>]
        example: help help

        shows help for the given command
        '''
        if args:
            hook = getattr(self, 'do_%s' % (args[0].lower(),), None)
            if hook:
                text = '\r\n'.join(textwrap.dedent(hook.__doc__).strip().splitlines())
                if kwargs.get('signle', False):
                    self.sendline(text.splitlines()[0])
                else:
                    self.sendline(text)
            else:
                self.sendline('command not found')

        else:
            return self.do_help('help')

    def do_history(self):
        '''
        syntax:  history

        shows the command history
        '''
        for i, command in enumerate(self.history):
            if i > 0:
                self.send('%d.\t%s\r\n' % (i, command))
        self.send(self.prompt)

    def do_exit(self, *args):
        '''
        syntax:  exit
        example: exit

        stop the scanner daemon
        '''
        self.send('bye\r\n')
        sys.exit(0)

    do_quit = do_exit

if __name__ == '__main__':
    import select

    con = Console()
    try:
        cli = CLI(socket=con)
        cli.is_running = True
        while cli.is_running:
            r, w, e = select.select([cli], [], [], 0.1)
            if r:
                cli.read()
    finally:
        con.restore()


