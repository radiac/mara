"""
Gender value for user

Used to generate pronouns
"""
from __future__ import unicode_literals

from ... import storage
from ..commands import define_command
from ..language.pronouns import MALE, FEMALE, OTHER


class GenderFieldDescriptor(object):
    """
    Descriptor to hold the gender value and ensure it's an object
    """
    def __init__(self, name):
        self.name = name
    
    def __get__(self, obj, type=None):
        if obj is None:
            return self
            
        value = getattr(obj, self.name, None)
        if value is None:
            return OTHER
        return value
        
    def __set__(self, obj, value):
        if obj is None:
            raise AttributeError('Cannot set gender on a class')
        
        if value not in (MALE, FEMALE):
            value = OTHER
        
        setattr(obj, self.name, value)
    
    def __delete__(self, obj):
        delattr(obj, self.name)


class GenderField(storage.Field):
    def contribute_to_class(self, store_cls, name):
        """
        Add a GenderFieldDescriptor to the object to hold the value
        """
        setattr(store_cls, name, GenderFieldDescriptor('_gender_%s' % name))


class GenderMixin(storage.Store):
    """
    Store gender
    """
    abstract = True
    gender = GenderField(default=OTHER)


@define_command(
    args=r'^(male|female|other|)$', syntax='[male|female|other]',
    help='Check or set your gender',
)
def cmd_gender(event, gender):
    gender = gender.lower()
    if not gender:
        event.user.write('Your gender is currently %s' % event.user.gender)
        return
    if gender not in (MALE, FEMALE):
        gender = OTHER
    event.user.gender = gender
    event.user.save()
    event.user.write('Your gender is now %s' % gender)
