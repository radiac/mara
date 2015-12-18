# -*- coding: utf-8 -*-
"""
Test the example chat server
"""
from __future__ import unicode_literals

from .lib import *
from examples import chat


class ChatTestService(TestService):
    def define(self):
        return chat.service

class ChatClient(Client):
    username_prompt = 'Welcome. What is your name? '

class ChatTest(TestCase):
    """
    Test the example chat server
    
    Multiple tests of same service to check service.stop() cleans up correctly.
    """
    def setUp(self):
        self.service = ChatTestService()
        
    def tearDown(self):
        self.service.stop()
    
    def test_single(self):
        "Test chat single connection"
        client = ChatClient(self)
        client.login('testuser')
        client.assertLine('Welcome, testuser')
        client.assertResponse('Hello', 'testuser> Hello')
        client.assertResponse('/me dances', 'testuser dances')
        client.assertResponse('/who', 'Users here at the moment:', '  testuser')
        client.assertResponse('/quit', 'Goodbye!')
        client.assertClosed()

    def test_multiple(self):
        "Test chat multiple connections"
        client1 = ChatClient(self)
        client1.login('ann')
        client1.assertLine('Welcome, ann')
        
        client2 = ChatClient(self)
        client2.login('bob')
        client2.assertLine('Welcome, bob')
        client1.assertLine('-- bob has connected --')
        
        client1.assertResponse('Hello', 'ann> Hello')
        client2.assertLine('ann> Hello')
        
        client1.assertResponse('/me dances', 'ann dances')
        client2.assertLine('ann dances')
        
        client1.assertResponse(
            '/who',
            'Users here at the moment:', '  ann', '  bob',
        )
        client2.assertNothing()
        
        client1.assertResponse('/quit', 'Goodbye!')
        client1.assertClosed()
        client2.assertLine('-- ann has disconnected --')
        
        client2.assertResponse('/quit', 'Goodbye!')
        client2.assertClosed()

    def test_unicode(self):
        "Test chat unicode"
        client = ChatClient(self)
        client.login('testuser')
        client.assertLine('Welcome, testuser')
        client.assertResponse('cash $£€ monies', 'testuser> cash $£€ monies')
        client.assertResponse(
            'niño, 男の子, เด็กผู้ชาย, garçon',
            'testuser> niño, 男の子, เด็กผู้ชาย, garçon'
        )
        client.assertResponse('/quit', 'Goodbye!')
        client.assertClosed()
