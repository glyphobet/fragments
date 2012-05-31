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

def colorize(line, color=None, colorblind=False):
    color_by_prefix = {
        '+' : (BLUE if colorblind else GREEN),
        '-' : RED,
        '@' : MAGENTA,
        '?' : MAGENTA,
        'M' : YELLOW ,
        'D' : RED    ,
        'A' : BLUE if colorblind else GREEN,
        'E' : GREY   ,
    }
    weight = NORMAL
    if color is None:
        color = color_by_prefix.get(line[0:1], WHITE)
    if line.startswith('diff '):
        color = BRIGHT_WHITE
        weight = BOLD
    if line.startswith('+++') or line.startswith('---'):
        weight = BOLD
    if color and sys.stdout.isatty():
        return '\033[%sm\033[%sm%s\033[0m' % (weight, color, line)
    else:
        return line
