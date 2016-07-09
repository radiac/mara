"""
Preposition operations
"""
from __future__ import unicode_literals

import operator
import re


PREPOSITIONS = [
    # take x P y
    'in', 'from',

    # put x P y
    # Also: in
    'on', 'by', 'over', 'under',

    # give x P y
    'to',

    # point x P y
    'at',
]

ALIASES = {
    'in': ['into', 'in to', 'through'],
    'from': ['off', 'out of'],
    'on': ['onto', 'on to'],
    'by': ['next to', 'beside'],
    'to': ['towards'],
    'over': ['above', 'across'],
    'under': ['below'],
}

# Generate regular expression to match these prepositions
SPLIT_RE = re.compile(r'^(.+?) +(%s) +(.+?)$' % (
    '|'.join([
        # Make sure that spaces can be any length
        word.replace(' ', ' +')
        for word in

        # Sort so that values with spaces appear first
        sorted(
            [PREPOSITIONS + reduce(operator.add, ALIASES.values())],
            key=lambda word: (' ' * word.count(' ')) + word
        )
    ])
))

# Generate reverse lookup for aliases
CANONICAL = {
    value: key
    for key, values in ALIASES.items()
    for value in values
}


def preposition_split(fragment):
    """
    Naieve method to split a sentence fragment by a preposition

    Expects a fragment in the format:
        (fragment) (known preposition) (fragment)

    Returns a tuple of (fragment, preposition, fragment), or raises
    ValueError if no preposition is found.

    Alias prepositions are converted to their canonical preposition
    """
    matches = SPLIT_RE.match(fragment, re.I)
    if not matches:
        raise ValueError("Unexpected sentence fragment")

    left, prep, right = matches.groups()
    return left, CANONICAL.get(prep, prep), right
