"""
Talker service
"""
from __future__ import unicode_literals

import datetime

import mara
from mara.timers.date import DateTimer


service = mara.Service()


# Defaults (explicit for clarity)
@service.timer(DateTimer, minute=0, second=0)
def church_bell(timer):
    hour = datetime.datetime.fromtimestamp(service.time).hour % 12
    if hour == 0:
        hour = 12
    service.write_all('A church bell in the distance chimes %d time%s.' % (
        hour, '' if hour == 1 else 's',
    ))
