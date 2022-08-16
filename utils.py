DIRECTIONS = {
    0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)
    # up right down left
}
WINDOW_SIZE = (1200, 800)
CELL_SIZE = (100, 100)
MARGIN = 3
BOARD_SIZE = (6, 8)
GROUP_ID_TEXTBOX_SIZE = (30, 30)
COMMAND_INPUT_FORBIDDEN_CHARS = list('/')
COMMAND_INPUT_HEIGHT = 40

UNITS = {'manipulator', 'portal', 'conveyorbelt', 'rock', 'initstack', 'stack', 'flipper', 'submitter'}
CONTROLLABLE_UNITS = {'manipulator', 'conveyorbelt', 'flipper'}

COMMAND_CHARACTERS = {
    't': None,
    'p': None,
    'c': None,
    'r': None,
    '+': None,
    '-': None,
    'f': None,
}


def inside_borders(pos):
    row, col = pos
    return 0 <= row < BOARD_SIZE[0] and 0 <= col < BOARD_SIZE[1]


def paint(s: str, color: str = '#FFFFFF', size=4):
    '''
    Returns html-colored with given color string s 
    '''
    return f'<font color={color} size={size}>{s}</font>'

