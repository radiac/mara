"""
Cletus events
"""

class Event(object):
    "Non-specific event"
    def __init__(self):
        self.stopped = False
        
        # Service will be added by service
        self.service = None
    
    def stop(self):
        """
        Stop the event from being passed to any more handlers
        """
        self.stopped = True

    def __str__(self):
        """
        Return this event as a string
        """
        return '[%s]: %s' % (self.__class__.__name__, self.__class__.__doc__)
