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
__version__   = '0.1.0'

import os
PACKAGE = os.path.basename(os.path.dirname(os.path.abspath(__file__)))

def version():
    return '%s, created by %s' % ('-'.join([PACKAGE, __version__]), __author__)

