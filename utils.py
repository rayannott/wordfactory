DIRECTIONS = {
    0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)
    # up right down left
}
WINDOW_SIZE = (1200, 800)
CELL_SIZE = (100, 100)
MARGIN = 3
BOARD_SIZE = (6, 8)
GROUP_ID_TEXTBOX_SIZE = (30, 30)
# COMMAND_INPUT_ALLOWED_CHARS = list('0123456789tpcrf+- ')
COMMAND_INPUT_FORBIDDEN_CHARS = list('/')
COMMAND_INPUT_HEIGHT = 40

CONTROLLABLE_UNITS = {'manipulator', 'conveyorbelt', 'flipper', 'swapper'}

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
    M, N = (12, 8)
    return 0 <= row < M and 0 <= col < N


def paint(s: str, color: str = '#FFFFFF', size=4):
    '''
    Returns html-colored with given color string s 
    '''
    return f'<font color={color} size={size}>{s}</font>'

# level2 COAT sol: 1tcpr 0+ 2trpc 1tccprrtcpr 0+ 2tcpr 1tcpc 0+ 2trpc 1trp 0+ 2trpcctccp
# level1 CAT sol: 1tcpr 0+ 2trpc 1tcpr 0+ 2trpc 1tcpr 0+ 2trpc
