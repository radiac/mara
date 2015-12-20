"""
Test library
"""
from __future__ import print_function
from __future__ import unicode_literals

import os
import socket
import telnetlib
import time
import threading
import unittest

import mara
from mara import styles
from mara.settings import defaults


__all__ = [
    # Constants
    'DEBUG', 'DEBUG_TN', 'ATTEMPT_MAX', 'ATTEMPT_SLEEP', 'ATTEMPT_TIMEOUT',
    'IMPOSSIBLE', 'NEWLINE', 'CWD', 'EXAMPLES_DIR', 
    
    # Useful vars and classes
    'thread_counter', 'unittest', 'TestCase', 'TestService', 'Client', 'hr',
]


# Debug everything that we do
DEBUG = False

# Debug everything that telnetlib does
DEBUG_TN = False

# Limits for attempting to start the server, and to connect to the server
ATTEMPT_MAX = 10
ATTEMPT_SLEEP = 0.1

# Timeout for socket reading
ATTEMPT_TIMEOUT = 1

# A string which will not be returned from the server
IMPOSSIBLE = '$$--__--$$'
NEWLINE = '\r\n'

# Example scripts expect themselves to be in the root path
# Find the examples dir and use that as the root path
CWD = os.getcwd()
EXAMPLES_DIR = os.path.join(CWD, 'examples')
if not os.path.isdir(EXAMPLES_DIR):
    raise ValueError('Examples dir not found')

# Global thread counter to generate unique ids
class ThreadCounter(object):
    def __init__(self):
        self.count = 0
    def get(self):
        self.count += 1
        return self.count
thread_counter = ThreadCounter()


class FakeClient:
    columns = 80
    class service:
        class settings:
            hr_sequence = '-'
            hr_state = None

def hr(*msg):
    return styles.hr(*msg).render(FakeClient(), styles.StatePlain())

class TestCase(unittest.TestCase):
    def assertLine(self, response, expected):
        """
        Assert equal, but stripping the trailing newline from response
        """
        if not response.endswith(NEWLINE):
            self.fail(
                (
                    'Response does not end in newline sequence: '
                    'expected "%s", received "%s"'
                ) % (expected, response)
            )
        return self.assertEqual(response[:-len(NEWLINE)], expected)


class TestService(object):
    """
    Wrapper for a Service instance being tested
    
    Pass settings on the constructor, or set them on the settings attribute
    """
    # Global settings
    settings = mara.settings.Settings(
        root_path=EXAMPLES_DIR,
        log='all' if DEBUG else False,
        settings_collect_args=False,
    )
    
    stores = property(lambda self: self.service.stores)
    
    def __init__(self, *args, **kwargs):
        """
        Create and run a service
        """
        # Give service a thread
        self.thread_id = thread_counter.get()
        
        # Create service
        self.service = self.define()
        
        # Collect settings
        new_settings = mara.settings.Settings(*args, **kwargs)
        if self.settings:
            self.settings.update(new_settings)
        else:
            self.settings = new_settings
        
        # Start service thread
        self._exception = None
        self.thread = threading.Thread(
            name="%s-%s" % (self.__class__.__name__, self.thread_id),
            target=self.run,
        )
        self.thread.daemon = True  # Kill with main process
        self.thread.start()
        
        # Wait for service to run (or fail)
        while (
            not self._exception
            and not getattr(self.service, 'server', None)
            and not getattr(self.service.server, 'running', False)
        ):
            time.sleep(ATTEMPT_SLEEP)
        
        # Catch exception
        if self._exception:
            self.thread.join()
            raise RuntimeError("Thread %s failed" % self.thread.name)
    
    def define(self):
        """
        Define the service
        """
        raise NotImplementedError('Test service must implement define()')
        
    def run(self):
        """
        Run the service. Call this as a thread target.
        """
        try:
            self.service.run(self.settings)
        except Exception as e:
            self._exception = e
            raise
    
    def stop(self):
        """
        Stop the service
        """
        self.service.stop()
        self.thread.join()



class Client(object):
    """
    Telnet client
    
    Wrapper for telnetlib.Telnet
    """
    username_prompt = 'Username: '
    password_prompt = 'Password: '
    
    def __init__(self, tests=None, host=defaults.host, port=defaults.port):
        """
        Create a connection to the client
        """
        self.tests = tests
        self.host = host
        self.port = port
        self.open()
    
    def open(self):
        """
        Create a connection to the client
        """
        # Try ATTEMPT_MAX times, in case socket isn't quite ready yet
        n = 0
        while n < ATTEMPT_MAX:
            n += 1
            try:
                self.tn = telnetlib.Telnet(self.host, self.port)
            except socket.error:
                time.sleep(ATTEMPT_SLEEP)
                if n == ATTEMPT_MAX:
                    raise
            else:
                break
        
        # Turn on telnetlib debugging
        if DEBUG_TN:
            self.tn.set_debuglevel(1)

    
    def close(self):
        self.tn.close()
    
    def write(self, *lines):
        """
        Write one or more lines
        """
        for line in lines:
            if DEBUG:
                print("test write>:", line)
            line += NEWLINE
            self.tn.write(line.encode('utf-8'))
    
    def read(self):
        """
        Read the next line
        """
        response = self.read_until(NEWLINE, timeout=ATTEMPT_TIMEOUT)
        if DEBUG:
            print("test read>:", response[:-len(NEWLINE)])
        return response
    
    # Map fns through to tn
    def read_until(self, expected, timeout=ATTEMPT_TIMEOUT):
        response = self.tn.read_until(expected.encode('utf-8'), timeout)
        return response.decode('utf-8')
    
    def read_all(self):
        return self.tn.read_all().decode('utf-8')


    #
    # Helper functions - common tasks
    #
    
    def assertNothing(self):
        """
        Assert that there is nothing to read
        """
        if not self.tests:
            raise ValueError('Cannot have a client assert without self.tests')
        self.tests.assertFalse(self.tn.sock_avail())
    
    def assertRead(self, line):
        """
        Assert that the exact response is received
        """
        if not self.tests:
            raise ValueError('Cannot have a client assert without self.tests')
        response = self.read_until(line, timeout=ATTEMPT_TIMEOUT)
        if DEBUG:
            print("test read> :", response)
        self.tests.assertEqual(response, line)
        
    def assertLine(self, *lines):
        """
        Assert that the specified response is received
        """
        if not self.tests:
            raise ValueError('Cannot have a client assert without self.tests')
        for line in lines:
            self.tests.assertLine(self.read(), line)
    
    def assertResponse(self, send, *lines):
        """
        Assert that the data sent receives the specified response
        """
        if not self.tests:
            raise ValueError('Cannot have a client assert without self.tests')
        self.write(send)
        self.assertLine(*lines)
    
    def assertClosed(self):
        if not self.tests:
            raise ValueError('Cannot have a client assert without self.tests')
        
        with self.tests.assertRaises(EOFError) as cm:
            self.read_until(IMPOSSIBLE, timeout=ATTEMPT_TIMEOUT)
        self.tests.assertEqual(str(cm.exception), 'telnet connection closed')
    
    def login(self, username, password=None):
        self.read_until(self.username_prompt)
        self.write(username)
        if password:
            self.read_until(self.password_prompt)
            self.write(password)
