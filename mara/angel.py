"""
Angel

Wrapper to start mara process, keep it running, and manage restarts
"""
from __future__ import unicode_literals

import multiprocessing
from multiprocessing.connection import Listener, Client
import os
import select
import socket
import subprocess
import sys
import time

from . import settings
from . import logger


# Commands sent by process to angel
CMD_GET_SERVICE = 'GET_SERVICE' # New process starting; get service from angel
CMD_SET_SERVICE = 'SET_SERVICE' # Old process stopping; send service to angel
CMD_STARTED = 'STARTED'         # New process has started
CMD_POLL = 'POLL'               # Process is checking in on angel
CMD_LOG = 'LOG'                 # Log a line from the process
CMD_OK = 'OK'                   # Command received and OK

# Start delay is doubled every time it fails, until it breaks this limit
# When 30, delays will be: 0, 1, 2, 4, 8, 16, 32, 32, 32, ...
START_DELAY_MAX = 30

# Time to wait after calling angel.stop(), to allow for the socket to release
STOP_DELAY = 0.1


class Angel(object):
    """
    The angel which manages mara script processes
    """
    args = None
    settings = None
    running = False
    active_process = None
    
    def __init__(self, *args, **kwargs):
        self.args = self.collect_args()
        self.settings = settings.collect(*args, **kwargs)
        
        # Move root_path to script's path
        if self.settings.root_path is None:
            # Get the dir name of the script, and either ensure it's an
            # absolute path, or join it to the cwd
            self.settings.root_path = os.path.abspath(
                os.path.dirname(self.args[0])
            )
        
        # Start logger
        self.log = logger.Logger(self.settings)
        self.log.force_with_pid()
    
    def collect_args(self):
        """
        Collect args for starting the Mara service
        """
        sys.argv.pop(0)
        if len(sys.argv) < 1:
            raise ValueError('First argument must be path to Mara service')
        return sys.argv

    def run(self):
        """
        Main angel loop
        """
        # Open angel socket
        authkey = self.settings.angel_authkey.encode('utf-8')
        listener = Listener(
            str(self.settings.get_path('angel_socket')),
            self.settings.angel_family,
            authkey=authkey,
        )
        multiprocessing.current_process().authkey = authkey
        
        # Give the listener a fileno so we can use it directly with select
        listener.fileno = listener._listener._socket.fileno
        
        # Main angel loop
        socket_to_process = {}
        process_to_socket = {}
        old_process = None
        start_delay = 0
        self.running = True
        while self.running:
            # We don't have an active process, so there shouldn't be others
            # If there are, terminate them
            for process, process_socket in list(process_to_socket.items()):
                if process.poll():
                    process.terminate()
                process_socket.close()
                del process_to_socket[process]
                del socket_to_process[process_socket]
            
            # There is nothing valid in the store
            # Either this is the first time it's running,
            # or it failed, so didn't get a chance to serialise anything
            store = None
            
            # Start script, with increasing delay if it last start failed
            if start_delay:
                time.sleep(start_delay)
                if start_delay < START_DELAY_MAX:
                    start_delay *= 2
            else:
                start_delay = 1
            self.active_process = self.start_process()
            
            # Loop while the script is running
            while self.active_process.poll() is None:
                # Check old processes for dead
                for process in process_to_socket.keys():
                    if process == self.active_process:
                        # Already checked active process
                        continue
                    if process.poll() is not None:
                        self.log.angel('Process %s has died' % process.pid)
                        process_to_socket[process].close()
                        del process_to_socket[process]
                        del socket_to_process[process_socket]
                
                # Check sockets for activity
                read_sockets = []
                send_sockets = []
                try:
                    read_sockets, send_sockets = select.select(
                        [listener] + list(socket_to_process.keys()), [], [], 1,
                    )[0:2]
                except select.error as e:
                    self.log.angel('Angel select error: %s' % e)
                except socket.error as e:
                    self.log.angel('Angel socket error: %s' % e)
                
                # Check listener socket for new connections
                if listener in read_sockets:
                    # Only leave process sockets on read_sockets
                    del read_sockets[read_sockets.index(listener)]
                    
                    # Accept the connection
                    process_socket = listener.accept()
                    
                    # Check this makes sense
                    if self.active_process in process_to_socket:
                        # We already have a socket for the active process.
                        # This shouldn't happen - only explanation is this is
                        # an intruder. Ignore it.
                        self.log.angel(
                            'New connection for existing process %s ignored' %
                            self.active_process.pid
                        )
                        process_socket.close()
                    
                    # Store against the current process
                    self.log.angel(
                        'Established connection to process %s' %
                        self.active_process.pid
                    )
                    socket_to_process[process_socket] = self.active_process
                    process_to_socket[self.active_process] = process_socket
                    
                # Check process sockets who want to say something
                for process_socket in read_sockets:
                    process = socket_to_process[process_socket]
                    try:
                        raw = process_socket.recv()
                    except Exception as e:
                        # We were told there would be something to read
                        process_socket.close()
                        try:
                            process.terminate()
                        except OSError:
                            # Already terminated
                            pass
                        del process_to_socket[process]
                        del socket_to_process[process_socket]
                        continue
                    
                    # Get command and data
                    if len(raw) == 2:
                        cmd, data = raw
                    else:
                        self.log.angel(
                            'Invalid data received from process %s' %
                            process.pid
                        )
                        cmd, data = None, None
                    
                    # Process cmd
                    if cmd == CMD_GET_SERVICE:
                        # Process has started and wants serialised data
                        process_socket.send((CMD_OK, store))
                        
                        if store is not None:
                            self.log.angel(
                                'Sent service to process %s' % process.pid
                            )
                        
                        # Empty store - can only be deserialised once
                        store = None
                        
                    elif cmd == CMD_SET_SERVICE:
                        # Process is sending us serialised service data
                        store = data
                        
                        # Process is now waiting for the OK before it stops.
                        # Don't send it yet - only stop once we get CMD_STARTED
                        # from the new process.
                        old_process = self.active_process
                        
                        self.log.angel(
                            'Received service from process %s' % process.pid
                        )
                        
                        # Start new process
                        self.active_process = self.start_process()
                        
                    elif cmd == CMD_STARTED:
                        # New process has started; cmd sent after PostStart
                        process_socket.send((CMD_OK, None))
                        
                        # It's not going to fall over immediately, reset delay
                        start_delay = 0
                        
                        # Tell old process it's ok to die now
                        if old_process:
                            if old_process in process_to_socket:
                                process_socket = process_to_socket[old_process]
                                process_socket.send((CMD_OK, None))
                            
                            self.log.angel(
                                'Process %s active, terminating process %s' % (
                                    process.pid, old_process.pid
                                )
                            )
                        else:
                            self.log.angel('Process %s active' % process.pid)

                    elif cmd == CMD_POLL:
                        process_socket.send((CMD_OK, None))
                    
                    elif cmd == CMD_LOG:
                        process_socket.send((CMD_OK, None))
                        self.log._write(data)
                        
                    else:
                        # Something has gone wrong - kill them
                        self.log.angel(
                            'Command not recognised, terminating process %s' %
                            process.pid
                        )
                        process_socket.close()
                        if process.poll() is None:
                            process.terminate()
                        del process_to_socket[process]
                        del socket_to_process[process_socket]
                        continue
            
            # Active process has died
            if self.running:
                # It died unexpectedly
                self.log.angel(
                    'Active process %s died unexpectedly' % self.active_process.pid
                )
            else:
                # We're shutting down
                self.log.angel(
                    'Active process %s terminating' % self.active_process.pid
                )
            
            if self.active_process in process_to_socket:
                # Clean up
                process_socket = process_to_socket[self.active_process]
                process_socket.close()
                del process_to_socket[self.active_process]
                del socket_to_process[process_socket]
    
    def start_process(self):
        """
        Start the Mara service in a separate process
        """
        process = subprocess.Popen([sys.executable] + self.args)
        self.log.angel('Starting process %s' % process.pid)
        return process
    
    def stop(self):
        """
        Terminate the current active process, wait for it to close, and stop
        the main angel loop
        """
        self.running = False
        
        if self.active_process.poll() is None:
            self.active_process.terminate()
            self.active_process.wait()
            # It should be ok, but give the system a moment to free the port
            time.sleep(STOP_DELAY)


class Process(object):
    """
    A process managed by an angel
    """
    def __init__(self, service):
        self.service = service
        self.settings = service.settings
        self.client = None
    
    @property
    def _log(self):
        return self.service.log
    
    def connect(self):
        """
        Try to connect to angel
        
        Returns True if connection is made, and instance evaluates to True
        Returns False if angel is not found, and instance evaluates to False
        """
        # Cannot log - service.log is defined based on outcome of this
        try:
            authkey = self.settings.angel_authkey.encode('utf-8')
            self.client = Client(
                str(self.settings.get_path('angel_socket')),
                self.settings.angel_family,
                authkey=authkey,
            )
            multiprocessing.current_process().authkey = authkey
        except socket.error:
            return False
        return True
    
    def _send_ok(self, cmd, data=None, log=None):
        """
        Send data to the angel and wait for the OK
        
        Return any response data received with the OK
        
        If angel fails, self.client will be cleared to None, so instance will
        evaluate to False
        """
        if not self.client:
            raise ValueError('Cannot send %s, not connected to angel' % cmd)
        try:
            self.client.send((cmd, data))
            # Now block and wait for the OK - this may take a while
            # The new process has to start and take over the sockets first
            ok, response = self.client.recv()
        except Exception as e:
            if cmd != CMD_LOG:
                self._log.service('Failed to %s with angel: %s' % (cmd, e))
            raise ValueError('Failed to %s with angel: %s' % (cmd, e))
        else:
            if ok == CMD_OK:
                return response
            self._log.service('Failed to get OK from angel')
            raise ValueError('Failed to get OK from angel')
        self.client = None
    
    def get_service(self):
        self._log.service('Asking angel for service')
        return self._send_ok(CMD_GET_SERVICE)
    
    def started(self):
        self._log.service('Informing angel service ready')
        self._send_ok(CMD_STARTED)
        
    def set_service(self, serialised):
        self._log.service('Sending service to angel')
        self._send_ok(CMD_SET_SERVICE, serialised)
    
    def poll(self):
        self._send_ok(CMD_POLL)
        
    def log(self, lines):
        self._send_ok(CMD_LOG, lines)
    
    def __bool__(self):
        return self.client is not None
    __nonzero__ = __bool__
