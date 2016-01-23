"""
Date timer

Requires dateutil module: pip install python-dateutil
"""
from __future__ import unicode_literals

import datetime

try:
    from dateutil.relativedelta import relativedelta
except ImportError as e:
    raise ImportError('%s - it is required for DateTimer' % e)

from .timer import Timer


DATE_UNITS = ['second', 'minute', 'hour', 'day', 'month', 'year']


class DateTimer(Timer):
    """
    A timer which will fire at the specified date and time combination

    Set a value to None to allow it to change. It is not timezone aware.
    """

    def __init__(
        self,
        year=None, month=None, day=None, hour=None, minute=0, second=0,
        context=None
    ):
        super(DateTimer, self).__init__(context=context)
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second

        # Create relative delta
        smallest = None
        for unit in DATE_UNITS:
            if getattr(self, unit) is None:
                smallest = unit
                break
        if smallest is None:
            self.relative = None
        else:
            self.relative = relativedelta(
                **{smallest + 's': 1}
            )

    def update(self):
        # Can't update if there's no relative delta
        if self.relative is None:
            self.due = None
            return

        # Start with current datetime
        current = datetime.datetime.fromtimestamp(self.service.time)

        # Build best guess at due datetime
        # Determined values stay constant, take None from current datetime
        kwargs = {}
        for unit in DATE_UNITS:
            val = getattr(self, unit)
            kwargs[unit] = getattr(current, unit) if val is None else val
        due = datetime.datetime(**kwargs)

        # It's probably in the past - increase by relative delta until it's not
        while due < current:
            due += self.relative

        # Convert back to timestamp
        self.due = (due - datetime.datetime(1970, 1, 1)).total_seconds()
