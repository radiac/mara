"""
Timer registry
"""
from __future__ import unicode_literals


class Registry(object):

    def __init__(self, service):
        self.service = service
        self.next = None

    def trigger(self):
        # Walk the chain and trigger all timers which are due or overdue
        while self.next and self.next.due <= self.service.time:
            # Pop timer from chain
            timer = self.next
            self.next = timer.next

            # Trigger timer, and add it back if still active
            timer.trigger()
            if timer.active:
                timer.update()
                self.insert(timer)

    def add(self, timer):
        """
        Add a new timer to the registry
        """
        # Give timer info about the registry and service
        timer.registered(self)

        # Update timer so it has the correct time
        timer.update()

        # Insert it into the chain
        self.insert(timer)

    def insert(self, timer):
        """
        Update timer and add into chain at appropriate position
        """
        # If the timer doesn't have a due time, can't add it
        if not timer.due:
            return

        # Loop the chain until we find one later than the due time
        prev = None
        next = self.next
        while next and next.due <= timer.due:
            prev = next
            next = next.next

        # Point timer at next
        timer.next = next

        # Update previous to point at timer
        if prev:
            prev.next = timer
        else:
            # No previous - this is the first one
            self.next = timer
