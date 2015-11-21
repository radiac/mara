"""
Mara process manager

Controls settings, server, and loaded modules
"""
from collections import defaultdict
import datetime
import inspect
import multiprocessing
from multiprocessing import connection as multiprocessing_connection
import os
import socket
import subprocess
import sys
import time

from .settings import collect as collect_settings
from .connection import Server
from .angel import Process
from . import logger
from . import events
from . import storage
from . import timers


class Service(object):
    """
    Service management
    """
    def __init__(self):
        # Store settings
        self.settings = None
        
        # Angel currently unknown
        self.angel = None
        
        # No server yet
        self.server = None
        
        # Store of stores
        self.stores = defaultdict(dict)
        
        # Consistent time for events and timers
        self.time = time.time()
        
        # Initialise events
        self.events = defaultdict(list)
        self._known_events = {}
        
        # Initialise timers
        self.timers = timers.Registry(self)
        
        # An empty log
        self.log = None
    
    datetime = property(
        fget = lambda self: datetime.datetime.fromtimestamp(self.time),
        doc = "Get the current time as a datetime object"
    )
    
    clients = property(lambda self: self.server._clients.values())
    
    
    #
    # Events
    #
    
    def listen(self, event_class, handler=None):
        """
        Bind a handler to the specified event class, and to its subclasses
        """
        # Called directly
        if handler:
            self._listen(event_class, handler)
            return

        # Called as a decorator
        def decorator(fn):
            self._listen(event_class, fn)
            return fn
        return decorator
        
    def _listen(self, event_class, handler):
        """
        Internal method to recursively bind a handler to the specified event
        class and its subclasses. Call listen() instead.
        """
        # Recurse subclasses. Do it before registering for this event in case
        # they're not known yet, then they'll copy handlers for this event
        for subclass in event_class.__subclasses__():
            self._listen(subclass, handler)
            
        # Register class
        self._ensure_known_event(event_class)
        self.events[event_class].append(handler)
    
    def _ensure_known_event(self, event_class):
        """
        Ensure the event class is known to the service.
        
        If it is not, inherit handlers from its first base class
        """
        # If known, nothing to do
        if event_class in self._known_events:
            return
        
        # If base class isn't an event, nothing to do
        base_cls = event_class.__bases__[0]
        if not isinstance(base_cls, events.Event):
            return
        
        # Ensure base class is known, and copy its handlers
        self._ensure_known_event(base_cls)
        self.events[event_class] = self.events[base_cls][:]
    
    def trigger(self, event):
        """
        Trigger the specified event
        """
        # Make sure we've seen this event class before
        self._ensure_known_event(event.__class__)
        
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
    # Timers
    #
    
    def timer(self, cls=timers.PeriodTimer, **kwargs):
        """
        Function decorator to define a timer
        """
        def wrap(fn):
            timer = cls(**kwargs)
            timer.fn = fn
            self.timers.add(timer)
            return fn
        return wrap


    #
    # Service-wide client operations
    #
    
    def write(self, clients, *data):
        """
        Send the provided lines to the given client, or list of clients
        """
        if not hasattr(clients, '__iter__'):
            clients = [clients]
        for client in clients:
            client.write(*data)
    
    def write_all(self, *data, **kwargs):
        """
        Send the provided lines to all active clients, as returned by get_all()
        
        Takes the same arguments as get_all()
        """
        # Get client list
        clients = self.get_all(**kwargs)
        
        # Write data to the clients
        for client in clients:
            client.write(*data)
    
    def get_all(self, **kwargs):
        """
        Get a list of clients, filtered by the global filter, a local filter
        and an exclude list
        """
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
            clients = filter_fn(self, clients, **kwargs)
        
        return clients
        
    
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
    
    def run(self, *args, **kwargs):
        """
        Collect settings and start the server
        """
        # Collect settings
        self.settings = collect_settings(*args, **kwargs)
        
        # Try to connect to angel, and initialise appropriate logger
        self.angel = Process(self)
        if self.angel.connect():
            self.log = logger.AngelLogger(self.settings, self.angel)
            self.log.service('Connected to angel')
        else:
            self.log = logger.Logger(self.settings)
            # Not running with angel - remove from log levels
            self.log.ignore_angel()
            self.log.update_prefix()
            self.log.service('No angel detected')
        
        # Inform that we're starting
        self.log.service('Service starting')
        self.trigger(events.PreStart())
        
        # Try to deserialise service from angel
        if self.angel:
            # Connected to angel
            serialised = self.angel.get_service()
            if serialised:
                self.deserialise(serialised)
                if self.angel:
                    self.angel.started()
                    self.log.service('Service restarted')
                    self.trigger(events.PostStart())
                    self.trigger(events.PostRestart())
            
            if not self.angel:
                self.log.service('Angel lost - aborting startup')
                return
            
            # Set up angel watcher - when the angel dies, we die too
            @self.timer(period=1)
            def angel_watcher(timer):
                self.angel.poll()
                if not self.angel:
                    self.log.service('Angel lost - terminating')
                    self.write_all('-- Angel lost --')
                    self.stop()
            
        # Start new server if no angel, or angel didn't have serialised service
        if not self.server:
            self.server = Server(self)
            self.trigger(events.PostStart())
        
        self.server.listen()
        
    def poll(self):
        """
        A poll from the server
        """
        # Update time
        self.time = time.time()
        
        # Call due and overdue timers
        self.timers.trigger()
    
    def stop(self):
        """
        Stop the server
        """
        self.trigger(events.PreStop())
        self.server.shutdown()
        self.log.service('Service stopped')
        self.trigger(events.PostStop())

    def restart(self):
        """
        Restart the process
        """
        if not self.angel:
            raise ValueError('Cannot restart, not connected to angel')
        
        # Send reset warning
        self.log.service('Service restarting')
        self.trigger(events.PreRestart())
        
        # Flush all client output buffers
        clients = self.get_all()
        for client in clients:
            client.flush()
        
        # Suspend server, so sockets will back up waiting for new process
        self.server.suspend()
        
        # Serialise
        serialised = self.serialise()
        
        # Send serialised service to angel and tell it we're stopping
        self.angel.set_service(serialised)
        
        # Terminate immediately
        self.log.service('Service terminating')
        sys.exit()

    def serialise(self):
        """
        Serialise to be passed to a new process
        """
        # Serialise the store of stores (with session data)
        store_data = defaultdict(dict)
        for store_name, store in self.stores.items():
            store_data[store_name] = store.manager.serialise(session=True)
        
        return {
            'server':    self.server.serialise(),
            'store_data': store_data,
        }

    def deserialise(self, serialised):
        """
        Deserialise a serialised service into this instance
        """
        # Deserialise store of stores (with session data)
        store_data = serialised['store_data']
        for store_name, data in store_data.items():
            store_cls = self.stores.get(store_name)
            if store_cls is None:
                self.log.store(
                    'Could not thaw store "%s" - no longer defined' % store_name
                )
                continue
            store_cls.manager.deserialise(data)
        
        # Restore server and clients
        self.server = Server(self, serialised=serialised['server'])
