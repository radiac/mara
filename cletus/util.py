"""
Useful functions
"""

import datetime
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


def detail_error():
    from traceback import print_exc, format_exception
    import sys
    return [
        e.strip() for e in
        format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
    ]

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
        
    def render(self, width=80):
        if not self.msg:
            return '-' * width
        
        return (" %s " % self.msg).center(width, '-')

def pretty_list(data):
    if not data:
        return ''
    last = data[-1]
    rest = data[:-1]
    if rest and last:
        last = ' and ' + last
    return ', '.join(rest) + last


time_units = ['day', 'hour', 'minute', 'second']
def pretty_age(seconds=None, now=None, then=None):
    if not seconds:
        seconds = now - then
    
    sec_delta = datetime.timedelta(seconds = now - then)
    age = dict(zip(
        time_units,
        [
            sec_delta.days,
            sec_delta.seconds // 3600,
            sec_delta.seconds // 60 % 60,
            sec_delta.seconds % 60
        ]
    ))
    for attr in time_units:
        if age[attr] > 0:
            return "%d %s%s ago" % (age[attr], attr, '' if age[attr]==1 else 's')
    return '0 seconds ago'
    