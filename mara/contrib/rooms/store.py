"""
Mara rooms
"""
from . import constants
from ... import container
from ... import storage 

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
        self.intro = intro
        self.desc = desc
        self.exits = exits
        self.clone = clone
        
        # Tell exits which room they're bound to
        if self.exits:
            self.exits.room = self
            
        # Would be nice to load saved data here, but we can't do that until
        # the service has collected its settings and we know where the store is

    def _post_start(self, event=None):
        """
        Try to load any saved data from disk
        """
        super(BaseRoom, self)._post_start(event)
        self.load()

    def gen_clone(self):
        """
        Clone room

        Used to generate per-user rooms
        """
        # Create new instance
        self.__class__(
            # Same key; not active so we don't overwrite original instance
            self.key, active=False,
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
        
        # Move the user in here and save
        user.room = self
        user.save()
        
        # Add the user to our list of users in the room
        self.users.append(user)
        
        # Show the intro, if set
        if self.intro:
            user.write(self.intro, '')
        
        # Show them the room
        user.write(self.desc, '')
        short = self.short
        if not short:
            short = 'in ' + self.name
        user.write('You are ' + short)
        
        # Tell them who else is here
        user.write(self.get_who(exclude=user.client))
        
        # Show them the exits
        user.write(self.exits.get_desc())
        
        # Tell other local users
        enter_msg = user.name
        if exit:
            enter_msg += ' enters'
            if exit.related and exit.related.direction:
                enter_msg += constants.ENTER_FROM[exit.related.direction]
            else:
                enter_msg += ' from ' + exit.source.name
        else:
            # Must have logged in or jumped to the room
            enter_msg += 'appears from nowhere'
        self.write_all(enter_msg, exclude=user)

    def exit(self, user, exit):
        """
        User leaves this room
        """
        # Remove the user from the room
        self.users.remove(user)
        
        # Clear the user's room, but don't save
        # That way if they're disconnecting they'll end up where they were
        # If they're moving they'll get their new room soon anyway
        user.room = None
        
        # Tell other local users
        exit_msg = user.name
        if exit:
            exit_msg += ' leaves ' + constants.EXIT_TO[exit.direction]
        else:
            # Must have logged in or jumped to the room
            exit_msg += 'disappears'
        self.write_all(exit_msg, exclude=user)
