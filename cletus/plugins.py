"""
Plugin management
"""

import os

from cletus.events import listen_factory, Event
import cletus.log as log

def RegistryType_factory(reg_list):
    """
    A metaclass to add classes to a registry list
    """
    class RegistryType(type):
        def __new__(cls, name, bases, dct):
            new_cls = super(RegistryType, cls).__new__(cls, name, bases, dct)
            
            if not dct.get('abstract', False):
                reg_list.append(new_cls)
            
            return new_cls
    return RegistryType


class PluginRegistry(object):
    def __init__(self, manager):
        self.manager = manager
        self.path = manager.settings.plugins
        self.reset()
    
    def reset(self):
        self.manager.events.call('reload')
        self._input_processors = []
    
    commands = property(lambda self: self._commands, doc="Commands")
        
    def load(self):
        log.plugin('Plugins loading')
        
        self.reset()
        
        # Don't load anything if there's nothing to load
        if not self.path:
            return
        
        # Define registry classes, bound to attributes on this instance
        class InputProcessor(object):
            __metaclass__ = RegistryType_factory(self._input_processors)
            abstract = True
        
        env_global = {
            'manager':  self.manager,
            'events':   self.manager.events,
            'listen':   listen_factory(self.manager.events),
            'InputProcessor':  InputProcessor
        }

        for plugin_file in self._find_files():
            log.plugin('Plugin found: %s' % plugin_file)
            try:
                execfile(plugin_file, env_global)
            except Exception, e:
                from traceback import print_exc, format_exception
                import sys
                exceptions = format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
                log.plugin(
                    'Plugin error: %s' % str(sys.exc_info()[0]), *exceptions
                )
        self.manager.events.call('init')
        
    def _find_files(self, path=None):
        """
        Get a list of all plugins
        Plugin filenames must start with a number and end in '.py'
        They are sorted alphanumerically
        """
        if not path:
            path = os.path.abspath(self.path)
        
        files = os.listdir(path)
        files.sort()
        found = []
        for file in files:
            if file in ['.', '..']:
                continue
                
            file_path = os.path.join(path, file)
            
            if os.path.isdir(file_path):
                if file[0].isdigit():
                    found += self._find_files(file_path)
                
            elif file[0].isdigit() and file.endswith('.py'):
                found.append(file_path)
                
        return found
