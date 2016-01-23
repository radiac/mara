"""
Extensions for users
"""
from __future__ import unicode_literals

from .exit import ExitError
from .room import BaseRoom
from ... import storage
from ... import events

__all__ = [
    'RoomUserMixin', 'RoomConnectHandler', 'room_restart_handler_factory',
]


class RoomUserMixin(storage.Store):
    """
    Mixin for a user store to associate a related Room
    """
    abstract = True
    room = storage.Field(default=None)

    def move(self, direction):
        """
        Try to move the user in specified direction to a new room
        """
        # User has to be in a room
        if not self.room:
            raise ValueError(
                'Cannot move user "%s" - they are not in a room' % self.name
            )

        # Check there's an exit in that direction
        if direction not in self.room.exits:
            self.write(self.room.exits.default)
            return

        # Try to use the exit
        try:
            self.room.exits[direction].use(self)
        except ExitError as e:
            self.write(str(e))

    def disconnected(self):
        """
        Clean up User object when a user disconnects
        """
        super(RoomUserMixin, self).disconnected()

        # If they aren't in a room, do nothing
        if not self.room:
            return

        # Remove user from the room - but put it back on the user so they'll
        # end up in the right place when they come back.
        room = self.room
        room.exit(self)
        self.room = room


class RoomConnectHandler(events.Handler):
    """
    Mixin for users.ConnectHandler which connects a user to a room

    Set default_room to the room for users when they first connect; can be a
    Room instance, or a room store key
    """
    # Default room to place new users
    default_room = None

    # Room store name; used to find room instance if default_room is a string
    room_store_name = 'room'

    def __init__(self, *args, **kwargs):
        if not self.default_room:
            raise ValueError('RoomConnectHandler requires a default_room')
        super(RoomConnectHandler, self).__init__(*args, **kwargs)

    def handler_90_user_connected(self, event):
        """
        Move user into a room
        """
        # Find the room they were last in
        room = self.user.room

        # If this is their first time, or their room no longer exists, room
        # will be None; set them to the default room
        if not room:
            room = self.default_room
            if not isinstance(room, BaseRoom):
                room = events.store(self.store_name).get(room)

        # Enter it
        room.enter(self.user)


def room_restart_handler_factory(user_store, default_room):
    """
    Generate a PostRestart event handler to ensure that all users are in valid
    rooms.

    Moves users who have lost their current room back to the default_room

    Example usage::

        service.listen(
            events.PostRestart, room_restart_handler_factory(User, room_lobby)
        )
    """
    def handler(event):
        for key, user in user_store.manager.active().items():
            if not user.room:
                user_store.service.log.store(
                    'User "%s" no longer in a room' % key
                )
                default_room.enter(user)
    return handler
