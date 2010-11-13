#! /usr/bin/env python
# 
#                         _______
#   ____________ _______ _\__   /_________       ___  _____
#  |    _   _   \   _   |   ____\   _    /      |   |/  _  \
#  |    /   /   /   /   |  |     |  /___/   _   |   |   /  /
#  |___/___/   /___/____|________|___   |  |_|  |___|_____/
#          \__/                     |___|
#  
#
# (c) 2010 Wijnand 'maze' Modderman-Lenstra - http://maze.io/
#

__author__    = 'Wijnand Modderman-Lenstra <maze@pyth0n.org>'
__copyright__ = '(C) 2010 Wijnand Modderman-Lenstra'
__license__   = 'MIT'
__url__       = 'http://code.maze.io/'


class History(list):
    def __init__(self, *args):
        super(History, self).__init__(*args)
        self.position = -1

    def append(self, *args):
        super(History, self).append(*args)
        self.reset()

    def reset(self):
        self.position = len(self) - 1

    def current(self):
        return self[self.position]

    def backward(self):
        self.position = max(0, self.position - 1)
        return self.current()

    def forward(self):
        self.position = min(len(self) - 1, self.position + 1)
        return self.current()

    def complete_backward(self, item):
        for line in iter(reversed(self)):
            if item in line:
                return line

    def complete_forward(self, item):
        for line in iter(self):
            if item in line:
                return line


class HistoryFile(History):
    def __init__(self, filename, mode='a'):
        self.filename = filename
        self.load()
        self.handle = open(filename, mode)

    def load(self):
        for line in file(self.filename):
            super(History, self).append(line.strip())

    def append(self, line):
        super(History, self).append(line)
        self.handle.write(''.join([line, '\n']))
        self.handle.flush()
