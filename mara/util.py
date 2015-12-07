"""
Useful functions
"""

import datetime
import re

def detail_error():
    from traceback import print_exc, format_exception
    import sys
    return [
        e.strip() for e in
        format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
    ]

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
