"""
Cletus process manager

Controls settings, server, and loaded modules
"""
from collections import defaultdict
import datetime
import inspect
from modulefinder import ModuleFinder
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
    def __init__(self, modules=None):
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

        # If we haven't been told which modules to manage, find the root of the
        # module which is creating the service
        if not modules:
            import inspect
            caller = inspect.currentframe().f_back
            module_name = caller.f_globals['__name__']
            if '.' in module_name:
                module_name = module_name.split('.', 1)[0]
            if module_name == 'cletus':
                raise ValueError('Cannot define service under cletus package')
            modules = [module_name]
        if 'cletus' in modules:
            raise ValueError('Cannot reload cletus modules')
        self.modules = modules

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
            clients = filter_fn(service, clients, **kwargs)
        
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
        frozen = self._reload_prepare()
        
        # Try to reload
        e = None
        try:
            self._reload_modules()
        except ImportError, e:
            pass
        
        self._reload_restore(frozen)
        
        # If reload failed, re-raise its error
        if e:
            raise e
        
    def _reload_prepare(self):
        """
        Prepare for reload by freezing stores and sending events
        """
        # Send reset warning
        self.trigger(events.PreRestart())
        
        # Serialise the store of stores (with session data)
        store_data = defaultdict(dict)
        for store_name, store in self.stores.items():
            store_data[store_name] = store.manager.serialise(session=True)
        
        # Clear out the service storage registry
        self.stores = defaultdict(dict)
        
        return store_data
        
    
    def _reload_modules(self):
        """
        Reload managed modules
        
        These are the modules named in the Service(modules=[]) list, or if that
        is not set, the base package 
        """
        # Generate list of module references that we're going to reload
        modules = []
        for module_name in self.modules:
            for module in sys.modules.values():
                if module.__name__.startswith(module_name):
                    modules.append(module)
        modules = set(modules)
        
        # Now find their dependencies
        dependencies = defaultdict([])
        for module in modules:
            # Find filename
            filename = module.__file__
            if filename.endswith('.pyc'):
                filename = filename[:-1]
            
            # Find modules it imports which we're going to reload
            finder = ModuleFinder()
            finder.run_script(filename)
            for imported_name in finder.modules.keys():
                if imported_name not in sys.modules:
                    continue
                imported_module = sys.modules[imported_name]
                if imported_module in modules:
                    dependencies[module].append(imported_module)
        
        # Reload modules
        while dependencies:
            # Find everything without a dependency
            reloadable = [
                module for module, deps in dependencies.items() if not deps
            ]
            
            # If nothing is reloadable, there must be circular dependencies
            if not reloadable:
                raise ImportError(
                    'Cannot reload - circular dependencies detected in %s' % 
                    sorted([d.__name__ for d in dependencies.keys()])
                )
            
            # Reload the reloadable
            for module in reloadable:
                reload(module)
            
            # Clean up dependencies
            reloaded = set(reloadable)
            cleaned = defaultdict([])
            for module, deps in dependencies.items():
                # Empty deps already processed
                if not deps:
                    continue
                
                # Remove processed from deps
                cleaned[module] = set(deps).difference(reloaded)
            dependencies = cleaned
        
    def _reload_restore(self, store_data):
        """
        Restore after reload
        """
        # Thaw store of stores (with session data)
        for store_name, data in store_data:
            store_cls = self.stores.get(store_name)
            if store_cls is None:
                self.log.store(
                    'Could not thaw store "%s" - no longer defined' % store_name
                )
                continue
            store_cls.manager.deserialise(data)
        
        self.trigger(events.PostRestart())

    def stop(self):
        """
        Stop the server
        """
        self.trigger(events.PreStop())
        self.server.shutdown()
        self.log.service('Service stopped')
        self.trigger(events.PostStop())
