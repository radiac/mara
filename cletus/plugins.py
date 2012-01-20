"""
Plugin management
"""

import os

from cletus.events import listen_factory, Event
import cletus.log as log
import cletus.util as util

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
        
        # Define the publics dict and @public decorator
        publics = {}
        def public(fn):
            publics[fn.__name__] = fn
            return fn
        
        # Load each plugin
        for file_path in self._find_plugins():
            log.plugin('Plugin found: %s' % file_path)
            
            # Set up a new environment
            env_global = {
                'publics':  publics,
                'public':   public,
                # ++ Move these into the manager
                'manager':  self.manager,
                'events':   self.manager.events,
                'Event':    Event,
                'listen':   listen_factory(self.manager.events),
                'util':     util
            }
            
            # Add in the publics
            env_global.update(publics)
            
            try:
                execfile(file_path, env_global)
            except Exception, e:
                log.plugin(
                    'Plugin error: %s' % e + "\n".join( util.detail_error() )
                )
        self.manager.events.call('init')
        
    def _find_plugins(self):
        """
        Get a list of all plugins
        They are sorted alphanumerically
        """
        # Get list of paths
        if isinstance(self.path, basestring):
            paths = [self.path]
        else:
            paths = self.path
            
        found = []
        for path in paths:
            path = os.path.abspath(path)
            found.extend( self._search_path(path) )
            
        return found
        
    def _load_list(self, path):
        """
        Load a plugin list
        """
        root = os.path.dirname(path)
        found = []
        f = open(path, 'r')
        for line in f:
            line = line.rstrip()
            if not line or line.startswith('#'):
                continue
            
            plugin_path = os.path.join(root, line)
            found.extend( self._search_path(plugin_path) )
        f.close()
        
        return found
        
    def _search_path(self, path):
        """
        Search a path for plugins
        Path can be a .py, .list or dir
        """
        if os.path.isfile(path):
            if path.endswith('.py'):
                return [path]
                
            elif path.endswith('.list'):
                return self._load_list(path)
                
            else:
                log.plugin('Plugin filetype unknown: %s' % path)
                
        elif os.path.isdir(path):
            return self._search_dir(path)
            
        else:
            log.plugin('Plugin not found: %s' % path)
        
        return []
        
    def _search_dir(self, dir):
        """
        Search a dir for plugins
        """
        files = os.listdir(dir)
        files.sort()
        found = []
        for file_name in files:
            if file_name in ['.', '..']:
                continue
                
            file_path = os.path.join(dir, file_name)
            
            if os.path.isdir(file_path):
                if file_name[0].isdigit():
                    found += self._find_files(file_path)
                
            elif file_name[0].isdigit() and file_name.endswith('.py'):
                found.append(file_path)
                
        return found
