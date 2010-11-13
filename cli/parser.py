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

import shlex


class Token(str):
    pass


class TokenPipe(Token):
    pass


class TokenRedirect(Token):
    pass


class TokenWord(Token):
    pass


def parse(line, posix=True):
    lexer = shlex.shlex(line, posix=posix)
    lexer.wordchars += ',./[]{}~!@$%^&*()-_=+:;'

    while True:
        token = lexer.get_token()
        if not token:
            break

        if token == '|':
            yield TokenPipe(token)

        elif token in ['<', '>']:
            yield TokenRedirect(token)

        else:
            yield TokenWord(token)

if __name__ == '__main__':
    line = 'this "is a" \'<\' |test \'with "pipes\' > redirect'

    for token in parse(line):
        print token.__class__.__name__, token
