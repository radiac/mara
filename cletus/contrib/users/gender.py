"""
Gender value for user

Used to generate pronouns
"""

from ... import storage

from ..commands import define_command, MATCH_STR


MALE = 'male'
FEMALE = 'female'
OTHER = 'other'

SUBJECT = {
    MALE:   'he',
    FEMALE: 'she',
    OTHER:  'they',
}

OBJECT = {
    MALE:   'him',
    FEMALE: 'her',
    OTHER:  'they',
}

POSSESSIVE = {
    MALE:   'his',
    FEMALE: 'her',
    OTHER:  'their',
}

SELF = {
    MALE:   'himself',
    FEMALE: 'herself',
    OTHER:  'themselves',
}


class Gender(object):
    def __init__(self, type):
        if type not in (MALE, FEMALE):
            type = OTHER
        self.type = type
        self.subject = SUBJECT[self.type]
        self.object = OBJECT[self.type]
        self.possessive = POSSESSIVE[self.type]
        self.self = SELF[self.type]
    
    def __str__(self):
        return self.type
    
    def __unicode__(self):
        return self.type
    
    def __eq__(self, other):
        if isinstance(other, Gender):
            other = other.type
        return self.type == other


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
            return Gender(OTHER)
        return value
        
    def __set__(self, obj, value):
        if obj is None:
            raise AttributeError('Cannot set gender on a class')
        if not isinstance(value, Gender):
            value = Gender(value)
        setattr(obj, self.name, value)
    
    def __delete__(self, obj):
        delattr(obj, self.name)


class GenderField(storage.Field):
    def contribute_to_class(self, store_cls, name):
        """
        Add a GenderFieldDescriptor to the object to hold the value
        """
        setattr(store_cls, name, GenderFieldDescriptor('_gender_%s' % name))

    def serialise(self, obj, name):
        gender = getattr(obj, name, None)
        if gender is None:
            return None
        return gender.type
    
    def deserialise(self, obj, name, data):
        setattr(obj, name, Gender(data))


class GenderMixin(storage.Store):
    """
    Store gender
    """
    abstract = True
    gender = GenderField(default=OTHER)


@define_command(
    args=MATCH_STR, syntax='<male|female|other>', help='Set your gender',
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
