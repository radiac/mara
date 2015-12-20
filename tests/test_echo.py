"""
Test the example echo server
"""
from __future__ import unicode_literals

from .lib import *
from examples import echo


class EchoTestService(TestService):
    def define(self):
        return echo.service
    
class EchoTest(TestCase):
    """
    Test the example echo server
    
    Multiple tests of same service to check service.stop() cleans up correctly.
    """
    def setUp(self):
        self.service = EchoTestService()
        
    def tearDown(self):
        self.service.stop()
    
    def test_single(self):
        "Test echo single connection"
        client = Client(self)
        client.assertResponse('Hello', 'Hello')
        client.close()

    def test_multiple(self):
        "Test echo multiple connections"
        client1 = Client(self)
        client2 = Client(self)
        client1.write('client1')
        client2.write('client2')
        client1.assertLine('client1')
        client2.assertLine('client2')
        client1.close()
        client2.close()
