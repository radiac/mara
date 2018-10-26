"""
Base protocol
"""
import six


__all__ = ['registry', 'Protocol']

registry = {}


class ProtocolType(type):
    def __init__(self, name, bases, dct):
        super(ProtocolType, self).__init__(name, bases, dct)
        if self.__name__ in registry:
            raise ValueError(
                'Protocol {} already defined'.format(self.__name__)
            )
        registry[self.__name__] = self


@six.add_metaclass(ProtocolType)
class Protocol(object):
    def __init__(self, client):
        self.client = client

    def connect(self):
        """
        Called on connection
        """
        pass

    def read(self, data):
        """
        Data has arrived - process it and return it for consumption
        """
        return data

    def write(self, *data, **kwargs):
        """
        Data to send - prepare it and put it on the send buffer
        """
        pass

    def disconnected(self):
        """
        Clean up this object once connection is terminated
        """
        self.client = None

    def serialise(self):
        return

    def deserialise(self):
        return