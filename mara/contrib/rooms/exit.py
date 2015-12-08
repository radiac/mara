"""
Mara room exits
"""
from . import constants
from ... import util


__all__ = ['Exits', 'Exit', 'FakeExit', 'ExitError']


class ExitError(Exception):
    """
    Error raised by Exit.use() when an exit is disabled.
    
    The exception message will be sent to the user.
    """


class Exit(object):
    """
    An exit holds a reference to the rooms it connects, and manages a user's
    movement between rooms, calling the room's enter() and exit() methods.
    """
    # No target or related exit yet
    _target = None
    _related = None
    
    def __init__(self, target, related=None):
        """
        Define an exit, with an optional related exit in the target room.
        
        Arguments:
        
        target      Room that the exit leads to. Can either be a ``Room``
                    instance, or the key value for a room that is yet to be
                    defined.
        
        related     Optional: the related exit is the other side of this exit
                    in the target room; for example, if this exit is north, the
                    related exit will (usually) be south.
        """
        self._target = target
        self._related = related
        
        # Variables set by Exits.__init__
        self.exits = None
        self.direction = None
    
    @property
    def target(self):
        """
        Look up target if it is a string, and cache value for future requests
        """
        target = self._target
        if isinstance(target, basestring):
            target = self.source.manager.get(target)
            if target is None:
                raise ValueError(
                    'Room "%s" exits %s to undefined room "%s"' % (
                        self.source.key, self.direction, self._target
                    )
                )
        self.__dict__['target'] = target
        return target
    
    @property
    def source(self):
        """
        Look up source room, and cache value for future requests
        """
        if not self.exits:
            raise ValueError(
                "Cannot resolve an Exit's source before it has been added to"
                "an Exits instance"
            )
        self.__dict__['source'] = self.exits.room
        return self.exits.room
    
    @property
    def related(self):
        """
        Try to find the related exit in the target room, and cache value for
        future requests
        """
        related = self._related
        if not related:
            # Look for related exit on target's exits
            for target_name, target_exit in self.target.exits.items():
                if target_exit.target == self.source:
                    related = target_exit
                    break
        self.__dict__['related'] = related
        return related
        
    def use(self, user):
        """
        Move the user from one room to another
        
        Can raise ExitError(msg) to show the message to the user and leave them
        in their current room.
        
        Normally call using user.move(direction)
        """
        if not self.source:
            raise ExitError("Exit not initialised")
        
        self.source.exit(user, self)
        user.write('You go %s' % self.direction)
        self.target.enter(user, self)
    
    def get_desc(self):
        return constants.DESC[self.direction]


class FakeExit(Exit):
    """
    A fake exit which leaves the user in their current room
    """
    def __init__(self, name, msg):
        """
        Define a fake exit
        
        Takes a single argument: the message to show when the user fails to
        leave
        """
        self.msg = msg

    def use(self, user):
        raise ExitError(self.msg)


class Exits(dict):
    default = 'You cannot go that way.'
    
    def __init__(self, desc=None, default=None, **kwargs):
        """
        Define and store a room's exits
        
        Acts as a dict, with directions as keys and the exits as values.
        
        Arguments:
            desc        Static description string for the exits in this room.
                        If not defined, will be built automatically by get_desc
            default     Message to show when a user tries to exit in
                        a direction without an exit. If not set, uses default
                        defined on class.
            <direction> Exit definition. The key must be one of the directions
                        defined in contrib.rooms.constants.DIRECTIONS; the
                        value must be an Exit instance.
        
        Example::
        
            Exits(
                "There are no visible exits here.",
                other="You bump into a wall.",
                north=FakeExit("You bump into a slimy wall."),
                up=Exit("room_above"),
            )
        """
        if default:
            self.default = default
        self.desc = desc
        
        # Validate and store exits in our dict
        for direction, exit in kwargs.items():
            # Validate argument
            if direction not in constants.DIRECTIONS:
                raise TypeError('Invalid direction "%s"' % direction)
            if not isinstance(exit, Exit):
                exit = Exit(exit)
            
            # Give the exit information that only we know
            exit.exits = self
            exit.direction = direction
            
            # Store in our dict
            self[direction] = exit
            
        # Variables set automatically by Room.__init__
        self.room = None
    
    def get_desc(self):
        """
        Return the description of exits in this room. If ``desc`` was
        provided to the constructor that will be returned, otherwise a string
        will be built with a list of the defined exits.
        
        Used to generate the enter message, and as the response for cmd_exits. 
        """
        if self.desc:
            return self.desc
        
        # Sort available directions by DIRECTIONS
        exits = sorted(
            self.items(),
            key=lambda pair: constants.DIRECTIONS_INDEX[pair[0]]
        )
        
        # Generate message
        if not exits:
            return "There are no exits."
            
        elif len(exits) == 1:
            direction, exit = exits[0]
            return "There is one exit %s." % exit.get_desc()
            
        return "There are exits %s." % util.pretty_list([
            exit.get_desc() for direction, exit in exits
        ])
