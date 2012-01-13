"""
Plugin management
"""

#
# Commands
#


env_local = {}
env_global = {
    'PluginBase':   PluginBase
}

# evalfile
exec(src, env_global, env_local)

print 'Local:', env_local.has_key('Test')
print 'Global:', env_global.has_key('Test')
print 'Registry:', registry

t = registry['Test']()
#
# Plugin loader
#

class PluginRegistry(object):
    def __init__(self, manager):
        self.manager = manager
        self.path = manager.settings.plugin_path
        self.reset()
    
    def reset(self):
        self._commands = {}
    
    commands = property(lambda self: self._commands, doc="Commands")
        
    def load(self):
        self.reset()
        
        # Command class defined here to register on the PluginRegistry instance
        class CommandType(type):
            def __new__(cls, name, bases, dct):
                new_cls = super(CommandType, cls).__new__(cls, name, bases, dct)
                
                if not dct.get('abstract', False):
                    self._commands[name] = new_cls
                
                return new_cls

        class Command(object):
            __metaclass__ = CommandType
            abstract = True
        
        env_local = {}
        env_global = {
            'manager':  self.manager,
            'Command':  Command
        }
        
        for plugin_file in find_plugins(path):
            execfile(plugin_file, env_global, env_local)
    
    def _find_files(path):
        """
        Get a list of all plugins
        Plugin filenames must start with a number and end in '.py'
        They are sorted alphanumerically
        """
        path = os.path.abspath(path)
        files = os.listdir(dir)
        files.sort()
        found = []
        for file in files:
            if file in ['.', '..']:
                continue
                
            file_path = os.path.join(path, file)
            
            if os.path.isdir(file_path):
                found += self._find_files(file_path)
                
            elif file.endswith('.py') and file[0].isdigit():
                found.append(file_path)
        return found
        

############################ OLD

import sys
import string
from traceback import print_exc, format_exception



class PluginError(Exception): pass

#
# Check that modules can be reloaded safely
# Based on http://www.elifulkerson.com/projects/python-dynamically-reload-module.php
#

def listf(data):
    buffer = ""
    for line in data:
        buffer = buffer + line + "\n"
    return buffer

def can_reload_single(module_name):
    # See if the module can be imported at all
    try:
        tmp = __import__(module_name)
    except:
        raise PluginError, 'Error importing module "%s"' % module_name

    # Use the imported module to determine its actual path
    pycfile = tmp.__file__
    modulepath = string.replace(pycfile, ".pyc", ".py")

    # Try to open the specified module as a file
    try:
        code = open(modulepath, 'rU').read()
    except:
        raise PluginError, 'Error opening file "%s"' % modulepath
    
    # See if the file we opened can compile
    try:
        compile(code, module_name, "exec")
    except:
        raise PluginError, 'Error compiling module: %s\r\n%s' % (
            str(sys.exc_info()[0]),
            listf(format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
        )
    else:
        # Will it execute
        try:
            execfile(modulepath, {})
        except:
            raise PluginError, 'Error executing module: %s\r\n%s' % (
                str(sys.exc_info()[0]),
                listf(format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
            )
    
    # Code compiled and executed without error
    return True


def can_reload(*module_names):
    for module_name in module_names:
        can_reload_single(module_name)
    return True


#
# Importer
#
def load(module_name, globals, locals):
    # Detect if it's already loaded
    old_module = sys.modules.get(module_name, False)

    # Test it's OK
    can_reload(module_name)
    
    # Load or reload
    if old_module:
        # Clear old attr
        for setting in dir(old_module):
            if not setting.startswith('_'):
                delattr(old_module, setting)
        
        reload(old_module)
    else:
        __import__(module_name, globals, locals)
        
    new_module = sys.modules[module_name]
    return new_module
    

def import_module(module_name, globals, locals):
    # Load the module
    new_module = load(module_name, globals, locals)
    
    # Import the module name
    globals[module_name] = new_module
    
def import_all(module_name, globals, locals):
    # Load the module
    new_module = load(module_name, globals, locals)

    # Import settings
    for setting in dir(new_module):
        if not setting.startswith('_'):
            globals[setting] = getattr(new_module, setting)

