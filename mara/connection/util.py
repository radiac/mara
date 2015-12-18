"""
Connection utils
"""
from __future__ import unicode_literals

from multiprocessing.reduction import reduce_handle, rebuild_handle
import socket

__all__ = ['serialise_socket', 'deserialise_socket']


def serialise_socket(socket):
    return reduce_handle(socket.fileno())

def deserialise_socket(serialised):
    fd = rebuild_handle(serialised)
    socket_object = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
    return socket.socket(_sock=socket_object)
