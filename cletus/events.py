"""
Cletus event manager
"""

import cletus.log as log

def listen_factory(registry):
    def decorator(name):
        def closed(fn):
            registry.listen(name, fn)
            return fn
        return closed
    return decorator

reserved = ['name', 'registry', 'manager', 'stop']
class Event(object):
    """
    Event object
    """
    def __init__(self, **kwargs):
        for (kwarg, val) in kwargs.items():
            if kwarg in reserved or kwarg[0] == '_':
                raise KeyError('The event argument %s is reserved for internal use' % kwarg)
            setattr(self, kwarg, val)
        
        self.name       = None
        self._stopped   = False
        self.registry   = None
        self.manager    = None
    
    def stop(self):
        """
        Stop the event from being passed to any more handlers
        """
        self._stopped = True

class EventRegistry(object):
    def __init__(self, manager):
        self.manager = manager
        self.reset()
    
    def reset(self):
        self.registry = {}
    
    def listen(self, name, handler):
        log.event('Event listener: %s -> %s()' % (name, handler.__name__))
        if not self.registry.has_key(name):
            self.registry[name] = []
        self.registry[name].append(handler)
    
    def unlisten(self, name, handler):
        if not self.registry.has_key(name):
            return
        self.registry[name].remove(handler)
    
    def call(self, name, event=None):
        log.debug('Event %s' % name)
        
        # Only bother calling if something has registered
        if not self.registry.has_key(name):
            return
        
        # Make sure we've got a clean Event
        if not event:
            event = Event()
        
        # Load the Event with relevant data
        event.name = name
        event.registry = self
        event.manager = self.manager
        
        # Call all listeners
        for handler in self.registry[name]:
            handler(event)
            if event._stopped:
                break
        