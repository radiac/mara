"""
Room constants
"""

# Standard directions
NORTH = 'north'
SOUTH = 'south'
EAST = 'east'
WEST = 'west'
NORTHEAST = 'northeast'
NORTHWEST = 'northwest'
SOUTHEAST = 'southeast'
SOUTHWEST = 'southwest'
UP = 'up'
DOWN = 'down'


# List of standard directions
# Used to validate exit keys and generate exit commands
DIRECTIONS = [
    NORTH, SOUTH, EAST, WEST,
    NORTHEAST, NORTHWEST, SOUTHEAST, SOUTHWEST,
    UP, DOWN,
]

# Build a lookup table - used for sorting partial lists of directions
DIRECTIONS_INDEX = {d: i for i, d in enumerate(DIRECTIONS)}


# Abbreviations for directions
# Used to generate exit command aliases
SHORT_DIRECTIONS = {
    'n':    NORTH,
    's':    SOUTH,
    'e':    EAST,
    'w':    WEST,
    'ne':   NORTHEAST,
    'nw':   NORTHWEST,
    'se':   SOUTHEAST,
    'sw':   SOUTHWEST,
}

# Descriptions for looking, entering, exiting
DESC = {d: 'to the %s' % d for d in DIRECTIONS}
DESC[UP] = 'up'
DESC[DOWN] = 'down'

EXIT_TO = {d: 'to the %s' % d for d in DIRECTIONS}
EXIT_TO[UP] = 'upwards'
EXIT_TO[DOWN] = 'downwards'

ENTER_FROM = {d: 'from the %s' % d for d in DIRECTIONS}
ENTER_FROM[UP] = 'from above'
ENTER_FROM[DOWN] = 'from below'

