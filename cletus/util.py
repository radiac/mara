"""
Useful functions
"""

import re

# Colour constants
COLOUR_BOLD = '\033[1m'
COLOUR_RESET = '\033[0m'
COLOUR_FORMAT = '\033[%dm'
COLOUR_CODES = zip(
    ['d','r','g','y','b','m','c','w'],
    range(30, 38)
)
COLOUR_NAMES = dict(zip(
    ['black','red','green','yellow','blue','magenta','cyan','white'],
    ['d','r','g','y','b','m','c','w'],
))

# Build regular expression replacements
COLOUR_RE = [
    (re.compile('^%s' % code), COLOUR_FORMAT % num) for (code, num) in COLOUR_CODES
] + [(re.compile('^^'), '^')]


def colourise(data):
    """
    Colourise a string
    Convert internal colour codes to ANSI colour codes
    """
    for (search, replace) in COLOURS_RE:
        data = search.sub(replace, data)
    return data + COLOUR_RESET


class HR(object):
    """
    Horizontal rule
    """
    def __init__(self, msg=None):
        self.msg = msg
        
    def render(self, width):
        if not self.msg:
            return '-' * width
        
        return (" %s " % self.msg).center(width, '-')
