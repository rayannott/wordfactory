DIRECTIONS = {
    0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)
    # up right down left
}
WINDOW_SIZE = (1200, 800)
CELL_SIZE = (80, 80)
# COMMAND_INPUT_ALLOWED_CHARS = list('0123456789tpcrf+- ')
COMMAND_INPUT_FORBIDDEN_CHARS = list('/')

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


def paint(s: str, color: str = '#FFFFFF'):
    '''
    Returns html-colored with given color string s 
    '''
    return f'<font color={color}>{s}</font>'

# level2 COAT sol: 1tcpr 0+ 2trpc 1tccprrtcpr 0+ 2tcpr 1tcpc 0+ 2trpc 1trp 0+ 2trpcctccp
# level1 CAT sol: 1tcpr 0+ 2trpc 1tcpr 0+ 2trpc 1tcpr 0+ 2trpc
