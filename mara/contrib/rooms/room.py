"""
Mara rooms
"""
from __future__ import unicode_literals

from . import constants
from .exit import Exits
from ... import container
from ... import storage 
from ... import styles

__all__ = ["BaseRoom"]



class RoomManager(storage.Manager):
    shared_cache = None
    def __init__(self):
        """
        Preload all rooms
        """
        super(RoomManager, self).__init__()
    
    def contribute_to_class(self, store_cls):
        """
        Create a shared cache between room subclasses
        
        This method will be called on concrete subclasses. The first concrete
        subclass will create a shared cache object, later subclasses will use
        that shared cache.
        
        This will mean that keys are shared between room classes, so exits
        can refer to any room class within that group of subclasses.
        """
        # Create and attach new manager instance as normal
        super(RoomManager, self).contribute_to_class(store_cls)
        
        # Share the cache
        if not self.shared_cache:
            # If we don't have a shared cache, we just duplicated ourselves
            # onto the first concrete room subclass.
            #
            # Use its instantiated cache for the shared cache
            store_cls.manager.shared_cache = store_cls.manager.cache
        else:
            # If we do have a shared cache, we are on a concrete subclass
            # somewhere below our first concrete room subclass.
            #
            # Give the new duplicate manager access to our shared cache.
            store_cls.manager.cache = self.shared_cache
    
    def deserialise(self, frozen, session=True):
        """
        Deserialise a serialised dict into active rooms
        
        Unlike the normal manager.deserialise, the rooms must already be
        defined.
        """
        for key, json in frozen.items():
            # Room must exist
            room = self.get(key)
            if not room:
                self.service.log.store('Room "%s" no longer defined' % key)
                continue
                
            # Update room with frozen data
            room.from_dict(json, session=session)
    

# Due to MRO, Store has to be first
class BaseRoom(storage.Store, container.ClientContainer):
    """
    Room store
    """
    abstract = True
    manager = RoomManager()
    
    # Don't save the users who are in this room; when the mud starts up, the
    # users won't be available. They'll add themselves if this is a restart.
    users = storage.Field(list, session=True)
    
    # Container clients are the users who are here
    clients = property(lambda self: [u.client for u in self.users])

    # Name of room
    # Used for titles and exits
    name = None

    # Short description
    # Used for room summary
    short = None

    # Intro, shown on entry to the room
    intro = None

    # Full room description, shown on entry (after intro) and look
    desc = None

    # Exits instance
    exits = None
    
    # If true, this room will be cloned for each user, and they will never
    # see or interact with each other
    clone = False

    def __init__(
        self, key, name,
        short=None, intro=None, desc=None, exits=None, clone=False,
        active=True,
    ):
        # Initialise store
        super(BaseRoom, self).__init__(key, active=active)
        
        # Store room instance arguments
        self.name = name
        self.short = short
        self.clone = clone
        
        # Introduction and description can be a single line, or lists of lines
        if isinstance(intro, basestring):
            intro = [line.strip() for line in intro.splitlines()]
        if isinstance(desc, basestring):
            desc = [line.strip() for line in desc.splitlines()]
        self.intro = intro
        self.desc = desc
        
        # Ensure exits is an Exits object - it may not be if loading from YAML
        # Exits is a subclass of dict
        if isinstance(exits, dict) and not isinstance(exits, Exits):
            exits = Exits(**exits)
        self.exits = exits
        
        # Tell exits which room they're bound to - unless they already know
        # their room, which would happen if this is a clone
        if self.exits and not self.exits.room:
            self.exits.room = self
            
        # Would be nice to load saved data here, but we can't do that until
        # the service has collected its settings and we know where the store is

    def _pre_start(self, event=None):
        """
        Try to load any saved data from disk
        """
        super(BaseRoom, self)._pre_start(event)
        self.load()

    def gen_clone(self):
        """
        Clone room

        Used to generate per-user rooms
        """
        # Create new instance
        return self.__class__(
            # Same key; not active so we don't overwrite original instance
            self.key, active=False,
            # Set clone to false now - we don't want to clone it again
            clone=False,
            # Copy everything except clone flag.
            name=self.name, short=self.short, intro=self.intro, desc=self.desc,
            # It's ok to reference the single self.exits - it's already bound
            exits=self.exits,
        )
    
    def filter_clients(self, filter_fn=None, exclude=None):
        """
        Filter by client or by user
        """
        if exclude is None:
            exclude = []
        elif not hasattr(exclude, '__iter__'):
            exclude = [exclude]
        exclude = [getattr(c, 'client', c) for c in exclude]
        return super(BaseRoom, self).filter_clients(filter_fn, exclude)
    
    def look(self, user, intro=False):
        """
        Show the user what is happening in the room
        
        If intro=True, show the intro message too
        """
        # Room name
        user.write(styles.bold(self.name)),
        
        # Show the intro, if set
        if intro and self.intro:
            user.write(*self.intro)
        
        # Main description
        if self.desc:
            user.write(*self.desc)
        
        # Tell them who else is here
        user.write(self.get_who(exclude=user.client))
        
        # Show them the exits
        user.write(self.exits.get_desc())

    def enter(self, user, exit=None):
        """
        User enters this room
        
        If exit is provided, it is the exit the user used to leave the source
        room; the related exit in this room is on exit.related (if one exists).
        """
        # Check if we should clone for the user
        if self.clone:
            room = self.gen_clone()
            room.enter(user, exit)
            return
        
        # Make sure the user isn't still in a room
        already_here = False
        if user.room:
            # See if they're reconnecting
            if user.room == self and user in self.users:
                already_here = True
            else:
                # Make them leave their current room
                user.room.exit(user)
        
        # Move the user in here and save
        user.room = self
        user.save()
        
        # Add the user to our list of users in the room
        if not already_here:
            self.users.append(user)
        
        # Show them the room, with intro
        self.look(user, intro=True)
        
        # Done if they were already here
        if already_here:
            return
        
        # Tell other local users
        enter_msg = user.name
        if exit:
            enter_msg += ' enters '
            if exit.related and exit.related.direction:
                enter_msg += constants.ENTER_FROM[exit.related.direction]
            else:
                enter_msg += 'from ' + exit.source.name
        else:
            # Must have logged in or jumped to the room
            enter_msg += ' appears from nowhere'
        self.write_all(enter_msg, exclude=user)

    def exit(self, user, exit=None):
        """
        User leaves this room
        """
        # Clear the user's room - don't save, they'll normally be going
        # somewhere, which will save anyway
        user.room = None
        
        # Check the user is actually in the room - may have been saved
        if user not in self.users:
            return
            
        # Remove the user from the room
        self.users.remove(user)
        
        # Tell other local users
        exit_msg = user.name
        if exit:
            exit_msg += ' leaves ' + constants.EXIT_TO[exit.direction]
        else:
            # Must have logged in or jumped to the room
            exit_msg += ' disappears'
        self.write_all(exit_msg, exclude=user)
    
    def get_short(self):
        short = self.short
        if not short:
            short = 'in the ' + self.name
        return short
