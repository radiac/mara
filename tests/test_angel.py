"""
Test the angel
"""
from __future__ import unicode_literals

import mara


###############################################################################
############################################################### Process
###############################################################################

if __name__ == '__main__':
    # test_angel.py run directly - has been called by the angel
    from examples import talker
    
    # Replace restart command so it doesn't require admin permission
    talker.commands.commands.unregister('restart')
    talker.commands.commands.register(
        'restart', mara.contrib.commands.cmd_restart,
    )
    
    talker.service.run()


###############################################################################
############################################################### Angel
###############################################################################

else:
    # test_angel.py imported - being called as a test
    
    import threading
    import shutil
    import os
    
    # Import lib and define constants here
    # It's a relative import, so can't import it if __main__ 
    from .lib import *
    ANGEL_SOCKET = os.path.join(EXAMPLES_DIR, 'test_angel.sock')
    TALKER_STORE = os.path.join(EXAMPLES_DIR, 'test_talker_store')
    
    
    class Angel(mara.angel.Angel):
        def collect_args(self):
            "Arguments for angel to start the service"
            return [
                # Service is in this file
                __file__,
                
                # Define settings - we have to do it here because we can't
                # access 
                '--root_path=%s' % EXAMPLES_DIR,
                '--angel_socket=%s' % ANGEL_SOCKET,
                '--store_path=%s' % TALKER_STORE,
                '--log=all' if DEBUG else '--no-log',
            ]
    
    
    class AngelThread(object):
        """
        Wrapper for managing an Angel in a thread
        
        Based on lib.TestService
        """
        def __init__(self):
            # Give service a thread using global tests.lib.thread_id
            self.thread_id = thread_counter.get()
            
            # Create angel
            self.angel = Angel(
                root_path=EXAMPLES_DIR,
                angel_socket=ANGEL_SOCKET,
                log='all' if DEBUG else False,
                settings_collect_args=False,
            )
        
            # Start service thread
            self._exception = None
            self.thread = threading.Thread(
                name="%s-%s" % (self.__class__.__name__, self.thread_id),
                target=self.run,
            )
            self.thread.daemon = True  # Kill with main process
            self.thread.start()
            
            # ++ wait for self.angel.active_process
            
            # Catch exception
            if self._exception:
                self.thread.join()
                raise RuntimeError("Thread %s failed" % self.thread.name)
        
        def run(self):
            """
            Run the angel. Call this as a thread target.
            """
            try:
                self.angel.run()
            except Exception as e:
                self._exception = e
                raise

        def stop(self):
            """
            Stop the angel
            """
            self.angel.stop()
            self.thread.join()


    from .test_talker import TalkerClient
    
    class AngelTest(TestCase):
        """
        Test the example talker using the angel
        """
        def remove_store(self):
            # Sanity check store so we don't delete the wrong thing
            if not TALKER_STORE or not CWD or not TALKER_STORE.startswith(CWD):
                raise ValueError('Invalid talker store')
            
            # Ensure test store doesn't exist
            if os.path.isdir(TALKER_STORE):
                shutil.rmtree(TALKER_STORE)
            
        def setUp(self):
            # Start service
            self.remove_store()
            self.angel = AngelThread()
            
        def tearDown(self):
            self.angel.stop()
            self.remove_store()
        
        def assertWho(self):
            self.ann.assertResponse(
                'who',
                hr('Currently online'),
                'ann\t0 seconds ago',
                'bob\t0 seconds ago',
                'cat\t0 seconds ago',
                hr(),
            )
            self.bob.assertNothing()
            self.cat.assertNothing()
            
        def test_multiple(self):
            "Test angel with multiple connections"
            # Create accounts
            self.ann = ann = TalkerClient(self)
            ann.create_account('ann', 'password1')
            ann.assertLine('Welcome, ann!', 'Nobody else is here.')
            
            self.bob = bob = TalkerClient(self)
            bob.create_account('bob', 'password2')
            bob.assertLine('Welcome, bob!', 'ann is here.')
            ann.assertLine('-- bob has connected --')
            
            self.cat = cat = TalkerClient(self)
            cat.create_account('cat', 'password3')
            cat.assertLine('Welcome, cat!', 'ann and bob are here.')
            ann.assertLine('-- cat has connected --')
            bob.assertLine('-- cat has connected --')
            
            # Confirm everything is working as expected
            self.assertWho()
            ann.assertResponse('say Hello', 'You say: Hello')
            bob.assertLine('ann says: Hello')
            cat.assertLine('ann says: Hello')
        
            # Issue the restart
            ann.assertResponse('restart', '-- Restarting server --')
            bob.assertLine('-- Restarting server --')
            cat.assertLine('-- Restarting server --')
            
            # Confirm everything is still working as expected
            self.assertWho()
            ann.assertResponse('say Hello', 'You say: Hello')
            bob.assertLine('ann says: Hello')
            cat.assertLine('ann says: Hello')
