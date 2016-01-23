"""
Pronoun mappings
"""
from __future__ import unicode_literals

import six


# First and second person
FIRST = 'first'
SECOND = 'second'
THIRD = 'third'

# Third person
MALE = 'male'
FEMALE = 'female'
OTHER = 'other'

SUBJECT = {
    FIRST: 'I',
    SECOND: 'you',
    MALE: 'he',
    FEMALE: 'she',
    OTHER: 'they',
}

OBJECT = {
    FIRST: 'me',
    SECOND: 'you',
    MALE: 'him',
    FEMALE: 'her',
    OTHER: 'them',
}

POSSESSIVE = {
    FIRST: 'my',
    SECOND: 'your',
    MALE: 'his',
    FEMALE: 'her',
    OTHER: 'their',
}

SELF = {
    FIRST: 'myself',
    SECOND: 'yourself',
    MALE: 'himself',
    FEMALE: 'herself',
    OTHER: 'themselves',
}

# Build lookup for third person pronouns: pronoun => (group, gender)
# Add THIRD to each group
THIRD_LOOKUP = {}
for _group in [SUBJECT, OBJECT, POSSESSIVE, SELF]:
    _group[THIRD] = {}
    for _gender in [MALE, FEMALE, OTHER]:
        _group[THIRD][_group[_gender]] = _gender
        THIRD_LOOKUP[_group[_gender]] = (_group, _gender)


@six.python_2_unicode_compatible
class Pronoun(object):
    """
    Set of pronouns for a given person
    """

    def __init__(self, type):
        self.type = type
        self.subject = SUBJECT[self.type]
        self.object = OBJECT[self.type]
        self.possessive = POSSESSIVE[self.type]
        self.self = SELF[self.type]

    def __str__(self):
        return self.type

    def __eq__(self, other):
        if isinstance(other, Pronoun):
            other = other.type
        return self.type == other


first = Pronoun(FIRST)
second = Pronoun(SECOND)
male = Pronoun(MALE)
female = Pronoun(FEMALE)
other = Pronoun(OTHER)
