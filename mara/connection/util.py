"""
Connection utils
"""
from __future__ import unicode_literals

from multiprocessing import reduction

import socket

__all__ = ['serialise_socket', 'deserialise_socket']


if hasattr(reduction, 'reduce_handle'):
    # Python 2.7, 3.2
    def serialise_socket(socket):
        return reduction.reduce_handle(socket.fileno())
        
elif hasattr(reduction, 'reduce_socket'):
    # Python 3.3
    def serialise_socket(socket):
        rebuild_fn, serialised = reduction.reduce_socket(socket)
        return serialised

elif hasattr(reduction, '_reduce_socket'):
    # Python 3.4+
    def serialise_socket(socket):
        rebuild_fn, serialised = reduction._reduce_socket(socket)
        return serialised

else:
    raise ImportError('Unknown multiprocessing API for reducing a socket')


if hasattr(reduction, 'rebuild_handle'):
    # Python 2.7, 3.2
    def deserialise_socket(serialised):
        fd = reduction.rebuild_handle(serialised)
        socket_object = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
        return socket.socket(_sock=socket_object)

elif hasattr(reduction, 'rebuild_socket'):
    # Python 3.3+
    def deserialise_socket(serialised):
        return reduction.rebuild_socket(*serialised)

elif hasattr(reduction, '_rebuild_socket'):
    # Python 3.4+
    def deserialise_socket(socket):
        rebuild_fn, serialised = reduction._rebuild_socket(socket)
        return serialised

else:
    raise ImportError('Unknown multiprocessing API for rebuilding a socket')
