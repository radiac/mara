"""
Test the example talker
"""
from __future__ import unicode_literals

from .lib import *
import os
import shutil

import mara
from examples import talker

TALKER_STORE = os.path.join(EXAMPLES_DIR, 'test_talker_store')


class TalkerTestService(TestService):
    settings = TestService.settings + mara.settings.Settings(
        store_path=TALKER_STORE,
    )
    def define(self):
        return talker.service

class TalkerClient(Client):
    username_prompt = 'What is your name? '
    password_prompt = 'Enter your password, or press enter to pick a new name: '
    
    def login(self, *args, **kwargs):
        super(TalkerClient, self).login(*args, **kwargs)
        self.assertLine('')
    
    def create_account(self, username, password):
        self.read_until(self.username_prompt)
        self.write(username)
        self.read_until('Do you want to create an account? (Enter yes or no) ')
        self.write('yes')
        self.read_until('Enter a password: ')
        self.assertResponse(password, '')
        self.assertRead('Confirm password: ')
        self.assertResponse(password, '', 'Account created!')
        
    def quit(self):
        self.assertResponse(
            'quit',
            hr('Goodbye!'),
        )
        self.assertClosed()


class TalkerTest(TestCase):
    """
    Test the example talker
    
    Multiple tests of same service to check service.stop() cleans up correctly.
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
        self.service = TalkerTestService()
        
    def tearDown(self):
        self.service.stop()
        self.remove_store()
    
    def test_account_create(self):
        "Test manual account creation in talker"
        client = TalkerClient(self)
        client.assertLine('Welcome to the Mara example talker!', '')
        client.assertRead('What is your name? ')
        client.assertResponse('ann', 'There is nobody with that name.')
        client.assertRead('Do you want to create an account? (Enter yes or no) ')
        client.assertResponse(
            'yes',
            'Please pick a password for your account.',
            'Your password must be at least 6 characters long.',
        )
        client.assertRead('Enter a password: ')
        client.assertResponse(
            'short', '', 'Your password must be at least 6 characters long.',
        )
        client.assertRead('Enter a password: ')
        client.assertResponse('password1', '')
        client.assertRead('Confirm password: ')
        client.assertResponse(
            'password1',
            '',
            'Account created!',
            'Welcome, ann!',
            'Nobody else is here.',
        )
        client.quit()
        
        # Check we can now log in
        client.open()
        client.login('ann', 'password1')
        client.assertLine('Welcome, ann!', 'Nobody else is here.')
        client.quit()
        
    def test_multiple(self):
        "Test talker multiple connections"
        # Create accounts
        ann = TalkerClient(self)
        ann.create_account('ann', 'password1')
        ann.assertLine('Welcome, ann!', 'Nobody else is here.')
        
        bob = TalkerClient(self)
        bob.create_account('bob', 'password2')
        bob.assertLine('Welcome, bob!', 'ann is here.')
        ann.assertLine('-- bob has connected --')
        
        cat = TalkerClient(self)
        cat.create_account('cat', 'password3')
        cat.assertLine('Welcome, cat!', 'ann and bob are here.')
        ann.assertLine('-- cat has connected --')
        bob.assertLine('-- cat has connected --')
        
        # Try private commands
        ann.assertResponse('admin', 'There are no admin users')
        ann.assertResponse(
            'commands',
            hr('Commands'), (
                'admin commands emote gender help look password quit say '
                'tell users who'
            ), hr(),
        )
        ann.assertResponse(
            'help',
            'Syntax: help <command>, or type commands to see a list of commands',
        )
        ann.assertResponse(
            'help commands',
            hr('Help: commands'),
            'List commands',
            '',
            'Syntax: commands (groups|<group>)',
            hr(),
        )
        ann.assertResponse(
            'who',
            hr('Currently online'),
            'ann\t0 seconds ago',
            'bob\t0 seconds ago',
            'cat\t0 seconds ago',
            hr(),
        )
        bob.assertNothing()
        cat.assertNothing()
        
        # Try commands which put something out to all
        ann.assertResponse('say Hello', 'You say: Hello')
        bob.assertLine('ann says: Hello')
        cat.assertLine('ann says: Hello')
        
        ann.assertResponse('emote is here', 'ann is here')
        bob.assertLine('ann is here')
        cat.assertLine('ann is here')
        
        ann.assertResponse('tell bob a secret', 'You tell bob: a secret')
        bob.assertLine('ann tells you: a secret')
        cat.assertNothing()
        
        ann.assertResponse(
            'tell bob, cat a secret', 'You tell bob and cat: a secret',
        )
        bob.assertLine('ann tells you and cat: a secret')
        cat.assertLine('ann tells you and bob: a secret')
        
        ann.assertResponse(
            'look',
            'bob and cat are here.',
        )
        bob.assertLine('ann looks around')
        cat.assertLine('ann looks around')
        
        ann.assertResponse('dance', 'You dance')
        bob.assertLine('ann dances')
        cat.assertLine('ann dances')
        
        ann.assertResponse('dance bob', 'You dance with bob')
        bob.assertLine('ann dances with you')
        cat.assertLine('ann dances with bob')
        
        # Pronoun social with gender other (default)
        ann.assertResponse('gender', 'Your gender is currently other')
        ann.assertResponse(
            'dance around bob, pointing at cat and ann',
            'You dance around bob, pointing at cat and yourself',
        )
        bob.assertLine('ann dances around you, pointing at cat and themselves')
        cat.assertLine('ann dances around bob, pointing at you and themselves')
        
        # Pronoun social with gender male
        ann.assertResponse('gender male', 'Your gender is now male')
        ann.assertResponse(
            'dance around bob, pointing at cat and ann',
            'You dance around bob, pointing at cat and yourself',
        )
        bob.assertLine('ann dances around you, pointing at cat and himself')
        cat.assertLine('ann dances around bob, pointing at you and himself')
        
        # Pronoun social with gender femmale
        ann.assertResponse('gender female', 'Your gender is now female')
        ann.assertResponse(
            'dance around bob, pointing at cat and ann',
            'You dance around bob, pointing at cat and yourself',
        )
        bob.assertLine('ann dances around you, pointing at cat and herself')
        cat.assertLine('ann dances around bob, pointing at you and herself')
