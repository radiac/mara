"""
Raw protocol
"""
import six

from .base import Protocol


class ProtocolRaw(Protocol):
    def read(self, data):
        return data

    def write(self, *data, **kwargs):
        for bytestring in data:
            if not isinstance(bytestring, six.binary_type):
                raise ValueError('Raw protocol can only send a byte string')
            self.client.send_buffer = bytestring
