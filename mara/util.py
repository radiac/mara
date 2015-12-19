"""
Useful functions
"""
from __future__ import unicode_literals

import datetime

TIME_UNITS = ['day', 'hour', 'minute', 'second']


def detail_error():
    from traceback import format_exception
    import sys
    return [e.strip() for e in format_exception(*sys.exc_info())]

def pretty_list(data):
    if not data:
        return ''
    last = data[-1]
    rest = data[:-1]
    if rest and last:
        last = ' and ' + last
    return ', '.join(rest) + last

def pretty_age(seconds=None, now=None, then=None):
    if not seconds:
        seconds = now - then
    
    sec_delta = datetime.timedelta(seconds = now - then)
    age = dict(zip(
        TIME_UNITS,
        [
            sec_delta.days,
            sec_delta.seconds // 3600,
            sec_delta.seconds // 60 % 60,
            sec_delta.seconds % 60
        ]
    ))
    for attr in TIME_UNITS:
        if age[attr] > 0:
            return "%d %s%s ago" % (age[attr], attr, '' if age[attr]==1 else 's')
    return '0 seconds ago'
