# -*- coding: utf-8
from __future__ import unicode_literals

import sys

GREY    = 30
RED     = 31
GREEN   = 32
YELLOW  = 33
BLUE    = 34
MAGENTA = 35
CYAN    = 36
WHITE   = 37
BRIGHT_WHITE = 57
NORMAL = 0
BOLD = 1


class ColoredString(type('')):
    color = WHITE
    weight = NORMAL
    def __str__(self):
        if sys.stdout.isatty():
            return '\033[%sm\033[%sm%s\033[0m' % (self.weight, self.color, super(ColoredString, self).__str__())
        else:
            return super(ColoredString, self).__str__()


class Added(ColoredString):
    color = GREEN

class Deleted(ColoredString):
    color = RED

class Modified(ColoredString):
    color = YELLOW

class LineNumber(ColoredString):
    color = MAGENTA

class Unknown(ColoredString):
    color = MAGENTA

class Error(ColoredString):
    color = GREY

class DeletedHeader(Deleted):
    weight = BOLD

class AddedHeader(Added):
    weight = BOLD

class Header(ColoredString):
    color = BRIGHT_WHITE
    weight = BOLD

class Prompt(ColoredString):
    color = YELLOW
    weight = BOLD

    def __new__(cls, s):
        return super(Prompt, cls).__new__(cls, s+' ')
