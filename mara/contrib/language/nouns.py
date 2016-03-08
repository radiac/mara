"""
Noun operations
"""
from __future__ import unicode_literals

import re


def plural_noun(noun, count=0):
    """
    Naieve method to pluralise a noun
    """
    if count == 1:
        return noun

    if noun.endswith(['s', 'x', 'z', 'ch', 'sh']):
        return noun + 'es'

    elif re.search('[^aeiou]y$', noun):
        return noun[:-1] + 'ies'

    return noun + 's'


def article_for_noun(noun):
    """
    Naieve method to return the indefinite article (a or an) for a noun

    Correct articles depend on the sound of the word; this returns based on
    the first character.
    """
    if noun.startswith(['a', 'e', 'i', 'o', 'u']):
        return 'an'
    return 'a'
