"""
Cletus process manager

Controls settings, server, and loaded modules
"""
from collections import defaultdict
import datetime
import inspect
import sys
import time

from .settings import Settings
from .settings import defaults as default_settings
from .connection import Server
from .logger import Logger
from . import events
from . import storage


class Service(object):
    """
    Service management
    """
    def __init__(self):
        # Store settings
        self.settings = None
        
        # No server yet
        self.server = None
        
        # Consistent time for events
        self.time = time.time()
        
        # Store of stores
        self.stores = defaultdict(dict)
        
        # An empty log
        self.log = None
        
        # Initialise events
        self.events = defaultdict(list)
        
    datetime = property(
        fget = lambda self: datetime.datetime.fromtimestamp(self.time),
        doc = "Get the current time as a datetime object"
    )
    
    clients = property(lambda self: self.server._clients.values())
    
    def run(self, *args, **kwargs):
        """
        Collect settings and start the service
        """
        # Collect settings
        self._collect_settings(*args, **kwargs)
        
        # Initialise service tools
        self.log = Logger(self.settings)
        
        # Start the server
        self._start()
        

    #
    # Events
    #
    
    def listen(self, event_class, handler=None):
        # Called directly
        if handler:
            return self.events[event_class].append(handler)

        # Called as a decorator
        def decorator(fn):
            self.events[event_class].append(fn)
            return fn
        return decorator
    
    def trigger(self, event):
        # Make sure all listeners have access to the service, in case they're
        # defined out of scope
        event.service = self
        
        self.log.event(event)
        for handler in self.events[event.__class__]:
            if event.stopped:
                return
            if inspect.isgeneratorfunction(handler):
                generator = handler(event)
                try:
                    generator.next()
                except StopIteration:
                    pass
                else:
                    if hasattr(event, 'client'):
                        event.client.capture(generator)
            else:
                handler(event)
    
    
    #
    # Server operations
    #
    
    def write(self, clients, *data):
        if not hasattr(clients, '__iter__'):
            clients = [clients]
        for client in clients:
            client.write(*data)
    
    def write_all(self, *data, **kwargs):
        # Capture kwargs
        filter_fn = kwargs.pop('filter', None)
        exclude = kwargs.pop('exclude', [])
        if kwargs:
            raise ValueError('Unexpected keyword arguments: %s' % kwargs)
        if not hasattr(exclude, '__iter__'):
            exclude = [exclude]
            
        # Filter the client list using global filter and exclude list
        clients = self.filter_all(
            self,
            (client for client in self.clients if client not in exclude),
            **kwargs
        )
        
        # Further filtering for this call
        if filter_fn:
            clients = filter_fn(service, clients, **kwargs)
        
        # Write data to the clients
        for client in clients:
            client.write(*data)
    
    @staticmethod
    def _filter_all_default(service, clients, **kwargs):
        return clients
    _filter_all = _filter_all_default
    
    @property
    def filter_all(self):
        return self._filter_all
    
    @filter_all.setter
    def filter_all(self, value):
        if value is None:
            value = self._filter_all_default
        elif not callable(value):
            raise ValueError('Filter must be a callable')
        self._filter_all = value
        
    
    #
    # Internal operations
    #
    
    def _collect_settings(self, *args, **kwargs):
        """
        Collect settings
        """
        # Start with default settings
        self.settings = Settings()
        self.settings.load(default_settings)
        
        # Load settings from fn arguments
        self.settings.load(*args)
        self.settings.update(kwargs)
        
        # Load settings from command line
        argv = sys.argv[1:]
        cmd_args = []
        cmd_kwargs = {}
        for arg in argv:
            if arg.startswith('--'):
                if '=' in arg:
                    key, val = arg[2:].split('=', 1)
                    cmd_kwargs[key] = val
                elif arg.startswith('--no-'):
                    cmd_kwargs[arg[5:]] = False
                else:
                    cmd_kwargs[args[2:]] = True
            else:
                cmd_args.append(arg)
        self.settings.load(*cmd_args)
        self.settings.update(cmd_kwargs)
    
    def _start(self):
        """
        Start the server
        """
        # Inform that we're starting
        self.log.service('Service starting')
        self.trigger(events.PreStart())
        
        # Start server
        self.server = Server(self)
        self.server.listen()
        self.trigger(events.PostStart())
        
    def poll(self):
        """
        A poll from the server
        """
        # Update time
        self.time = time.time()
    
    def reload(self):
        """
        Reset events and reload plugins
        """
        raise NotImplemented('Service cannot reload yet')

        # Send reset warning
        self.trigger(events.PreRestart())
        
        # Freeze the store of stores (with session data)
        frozen_stores = defaultdict(dict)
        for cls, stores in self.stores:
            frozen_stores[cls._store_name] = {
                key: store.to_dict(session=True)
                for key, store in stores.items()
            }
        self.stores = defaultdict(dict)
        
        # Reset the store registry, so it's clean for code to register stores
        storage.registry.clear()
        
        # ++ Reload modules
        
        # Thaw store of stores (with session data)
        for cls_name, stores in frozen_stores:
            cls = storage.registry.get(cls_name)
            if cls is None:
                self.log.store(
                    'Could not thaw store "%s" - no longer defined' % cls_name
                )
                continue
            self.stores[cls] = {
                key: cls(self, key).from_dict(store, session=True)
                for key, store in stores.items()
            }
        self.trigger(events.PostRestart())

    def stop(self):
        """
        Stop the server
        """
        self.trigger(events.PreStop())
        self.server.shutdown()
        self.log.service('Service stopped')
        self.trigger(events.PostStop())
