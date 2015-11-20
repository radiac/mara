"""
Collect settings
"""
import sys

from .container import Settings
from . import defaults


def collect(*args, **kwargs):
    """
    Collect settings
    """
    # Start with default settings
    settings = Settings()
    settings.load(defaults)
    
    # Load settings from fn arguments
    settings.load(*args)
    settings.update(kwargs)
    
    # We may have been told to not collect command line arguments
    if not settings.settings_collect_args:
        return settings
    
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
    settings.load(*cmd_args)
    settings.update(cmd_kwargs)
    
    return settings
