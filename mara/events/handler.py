"""
Handler class
"""
from __future__ import unicode_literals

import inspect
import six

__all__ = ['Handler']


class HandlerType(type):
    def __init__(self, name, bases, dct):
        super(HandlerType, self).__init__(name, bases, dct)

        # Collect handler functions, sorted by name
        self._handlers = [
            getattr(self, handler_name) for handler_name in sorted(dir(self))
            if handler_name.startswith('handler_')
        ]

        # Inherit missing docstrings
        if not self.__doc__:
            docbases = bases[:]
            for base in docbases:
                if issubclass(Handler, base):
                    # Either Handler or one of its bases - gone too far
                    continue
                if base.__doc__:
                    self.__doc__ = base.__doc__
                    break


@six.add_metaclass(HandlerType)
class Handler(object):
    """
    Class-based event handler
    """
    # Permanent list of all ordered handlers
    _handlers = None

    # Temporary handler queue, created for each event
    handlers = None

    # Reference to current event
    event = None

    def get_handlers(self):
        return self._handlers[:]

    def __call__(self, event, *args, **kwargs):
        """
        Run all handlers
        """
        # Prepare handler args and context
        self.args = args
        self.kwargs = kwargs
        self.event = event

        # Load up clean queue of handlers and loop until they're all run
        self.handlers = self.get_handlers()
        while self.handlers:
            # Get next handler
            handler = self.handlers.pop(0)

            # Process
            if inspect.isgeneratorfunction(handler):
                # ++ python 3.3 has yield from
                generator = handler(self, event, *self.args, **self.kwargs)
                try:
                    next(generator)
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
                handler(self, event, *self.args, **self.kwargs)

            # Option to terminate event
            if event.stopped:
                self.handlers = []

        # Clean up
        self.clean()

    def clean(self):
        """
        Clean the class after a __call__
        """
        self.event = None
        self.handlers = []

    def extend(self, mixin):
        """
        Extend this instance of this handler by adding the mixin to its base
        classes
        """
        self.__class__ = type(
            str('{}{}'.format(mixin.__name__, self.__class__.__name__)),
            (mixin, self.__class__), {},
        )
