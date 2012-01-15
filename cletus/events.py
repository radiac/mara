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

reserved = ['name', 'handled', 'registry', 'manager']
class Event(object):
    """
    Event object
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        
        for (kwarg, val) in kwargs.items():
            if kwarg in reserved:
                raise KeyError('The event argument %s is reserved for internal use' % kwarg)
            setattr(self, kwarg, val)
        
        self.name       = None
        self.handled    = False
        self.registry   = None
        self.manager    = None

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
        if not self.registry.has_key(name):
            return
        
        event.name = name
        event.registry = self
        event.manager = self.manager
        
        for handler in self.registry[name]:
            handler(event)
            if event.handled:
                break
        