"""
Timers
"""
from __future__ import unicode_literals

class Registry(object):
    def __init__(self, service):
        self.service = service
        self._next = None
    
    def get_next(self):
        if self._next.time <= self.service.time:
            yield self._next


class Timer(object):
    def __init__(self):
        pass
