"""
Handler class
"""
import inspect

__all__ = ['Handler']


class HandlerType(type):
    def __init__(self, name, bases, dct):
        super(HandlerType, self).__init__(name, bases, dct)
        
        # Collect handler functions, sorted by name
        self._handlers = [
            getattr(self, handler_name) for handler_name in sorted(dir(self))
            if handler_name.startswith('handler_')
        ]


class Handler(object):
    """
    Class-based event handler
    """
    __metaclass__ = HandlerType
    
    # Permanent list of all ordered handlers
    _handlers = None
    
    # Temporary handler queue, created for each event
    handlers = None
    
    # Reference to current event
    event = None
    
    def get_handlers(self):
        return self._handlers[:]
    
    def __call__(self, event, *args, **kwargs):
        # Load up clean queue of handlers and loop until they're all run
        self.event = event
        self.handlers = self.get_handlers()
        while self.handlers:
            # Get next handler
            handler = self.handlers.pop(0)
            
            # Process
            if inspect.isgeneratorfunction(handler):
                # ++ python 3.3 has yield from
                generator = handler(self, event, *args, **kwargs)
                try:
                    generator.next()
                except StopIteration:
                    pass
                else:
                    while True:
                        try:
                            try:
                                raw = yield
                            except Exception as e:
                                generator.throw(e)
                            else:
                                generator.send(raw)
                        except StopIteration:
                            break
                # ++ end python 2.7 support
            else:
                handler(self, event, *args, **kwargs)
            
            # Option to terminate event
            if event.stopped:
                self.handlers = []
        
        # Clean up
        self.event = None
        self.handlers = []
