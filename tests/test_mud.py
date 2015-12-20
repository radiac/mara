"""
Test the example mud
"""
from __future__ import unicode_literals

from .lib import *
import mara
import os
import shutil

from examples import mud
from examples.mud.rooms import room_lobby

MUD_STORE = os.path.join(EXAMPLES_DIR, 'test_mud_store')


class MudTestService(TestService):
    settings = TestService.settings + mara.settings.Settings(
        store_path=MUD_STORE,
    )
    def define(self):
        return mud.service

class MudClient(Client):
    username_prompt = 'What is your name? '
    password_prompt = 'Enter your password, or press enter to pick a new name: '
    
    def login(self, *args, **kwargs):
        super(MudClient, self).login(*args, **kwargs)
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


class MudTest(TestCase):
    """
    Test the example mud
    """
    def remove_store(self):
        # Sanity check store so we don't delete the wrong thing
        if not MUD_STORE or not CWD or not MUD_STORE.startswith(CWD):
            raise ValueError('Invalid talker store')
        
        # Ensure test store doesn't exist
        if os.path.isdir(MUD_STORE):
            shutil.rmtree(MUD_STORE)
        
    def setUp(self):
        # Start service
        self.remove_store()
        self.service = MudTestService()
        
    def tearDown(self):
        self.service.stop()
        self.remove_store()
    
    def create_accounts(self):
        """
        Create accounts for 3 users
        """
        ann = MudClient(self)
        ann.create_account('ann', 'password1')
        ann.assertLine(
            room_lobby.name,
            room_lobby.desc[0],
            'Nobody else is here.',
            'There are exits to the north, to the south and to the east.',
        )
        
        bob = MudClient(self)
        bob.create_account('bob', 'password2')
        bob.assertLine(
            room_lobby.name,
            room_lobby.desc[0],
            'ann is here.',
            'There are exits to the north, to the south and to the east.',
        )
        ann.assertLine(
            '-- bob has connected --',
            'bob appears from nowhere'
        )
        
        cat = MudClient(self)
        cat.create_account('cat', 'password3')
        cat.assertLine(
            room_lobby.name,
            room_lobby.desc[0],
            'ann and bob are here.',
            'There are exits to the north, to the south and to the east.',
        )
        ann.assertLine(
            '-- cat has connected --',
            'cat appears from nowhere',
        )
        bob.assertLine(
            '-- cat has connected --',
            'cat appears from nowhere',
        )
        
        return ann, bob, cat
    
    
    def test_rooms(self):
        """
        Test rooms, exits, movement and clone rooms
        """
        # Collect yaml rooms
        room_pool = self.service.stores['room'].manager.get('pool')
        clone_zone = self.service.stores['room'].manager.get('clone_zone')
        
        # Create accounts
        ann, bob, cat = self.create_accounts()
        
        # Check commands work to all in room
        ann.assertResponse('say Hello', 'You say: Hello')
        bob.assertLine('ann says: Hello')
        cat.assertLine('ann says: Hello')
        
        ann.assertResponse('dance', 'You dance')
        bob.assertLine('ann dances')
        cat.assertLine('ann dances')
        
        # Fake exit
        ann.assertResponse(
            'south',
            "You think about leaving, but decide it's nice here.",
        )
        bob.assertNothing()
        cat.assertNothing()
        
        # Exit north
        ann.assertResponse(
            'north',
            'You go north',
            room_pool.name,
            room_pool.desc[0],
            'Nobody else is here.',
            'There is one exit to the south.',
        )
        bob.assertLine('ann leaves to the north')
        cat.assertLine('ann leaves to the north')
        
        # Commands only work in the room
        ann.assertResponse('say Hello', 'You say: Hello')
        bob.assertNothing()
        cat.assertNothing()
        
        # Socials only work in the room
        ann.assertResponse('dance', 'You dance')
        bob.assertNothing()
        cat.assertNothing()
        
        # Return south
        ann.assertResponse(
            'south',
            'You go south',
            room_lobby.name,
            room_lobby.desc[0],
            'bob and cat are here.',
            'There are exits to the north, to the south and to the east.',
        )
        bob.assertLine('ann enters from the north')
        cat.assertLine('ann enters from the north')

        # Ann enters the clone zone
        ann.assertResponse(
            'east',
            'You go east',
            clone_zone.name,
            clone_zone.intro[0],
            clone_zone.desc[0],
            'Nobody else is here.',
            'There is one exit to the west.',
        )
        bob.assertLine('ann leaves to the east')
        cat.assertLine('ann leaves to the east')
        
        # Bob enters the clone zone
        bob.assertResponse(
            'east',
            'You go east',
            clone_zone.name,
            clone_zone.intro[0],
            clone_zone.desc[0],
            'Nobody else is here.',
            'There is one exit to the west.',
        )
        ann.assertNothing()
        cat.assertLine('bob leaves to the east')

        # Ann and bob are alone in the clone zone
        ann.assertResponse(
            'look',
            clone_zone.name,
            # Look ma, no intro
            clone_zone.desc[0],
            'Nobody else is here.',
            'There is one exit to the west.',
        )
        ann.assertResponse('say Hello', 'You say: Hello')
        bob.assertNothing()
        cat.assertNothing()
        
        # Return from the cold
        ann.assertResponse(
            'west',
            'You go west',
            room_lobby.name,
            room_lobby.desc[0],
            'cat is here.',
            'There are exits to the north, to the south and to the east.',
        )
        bob.assertNothing()
        cat.assertLine('ann enters from the east')

