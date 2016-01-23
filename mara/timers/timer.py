"""
Timer classes
"""
from __future__ import unicode_literals

import random


class Timer(object):
    """
    Base class for timers which fire at the specified time
    """
    service = None
    next = None
    fn = None
    active = True

    def __init__(self, due=None, context=None):
        self.due = due
        self.context = context

    def registered(self, registry):
        """
        Called when the timer is added to the registry
        """
        self.registry = registry
        self.service = registry.service

    def update(self):
        """
        Update the due time

        Set due to None to remove timer
        """
        pass

    def trigger(self):
        if self.fn:
            self.fn(self)
        else:
            self.stop()

    def stop(self):
        self.active = False


class PeriodTimer(Timer):
    """
    A timer which will fire after a given period
    """

    def __init__(self, period, context=None):
        super(PeriodTimer, self).__init__(context=context)
        self.period = period

    def update(self):
        if not self.due:
            self.due = self.service.time
        self.due += self.period


class RandomTimer(Timer):
    """
    A timer which will fire between a minimum and maximum period
    """

    def __init__(self, min_period, max_period, context=None):
        super(RandomTimer, self).__init__(context=context)
        self.min_period = min_period
        self.max_period = max_period

    def update(self):
        if not self.due:
            self.due = self.service.time
        self.due += random.randrange(self.min_period, self.max_period)
