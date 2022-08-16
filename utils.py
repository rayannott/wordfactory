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

UNITS = {'manipulator', 'portal', 'conveyorbelt', 'rock',
         'initstack', 'stack', 'flipper', 'submitter', 'card', 'piston'}
CONTROLLABLE_UNITS = {'manipulator', 'conveyorbelt', 'flipper', 'piston'}


def inside_borders(pos):
    row, col = pos
    return 0 <= row < BOARD_SIZE[0] and 0 <= col < BOARD_SIZE[1]


def paint(s: str, color: str = '#FFFFFF', size=4):
    '''
    Returns html-colored with given color string s 
    '''
    return f'<font color={color} size={size}>{s}</font>'


HELP_TEXT = {
    'rules': 'bla bla bla',
    'manipulator': '',
    'portal': '',
    'conveyorbelt': '',
    'rock': '',
    'initstack': '',
    'stack': '',
    'flipper': '',
    'submitter': '',
    'card':  '',
    'piston': ''
}


def help_commands_processing(raw_command: str):
    command = raw_command[4:].strip()
    if command in HELP_TEXT:
        return f'---{paint(command.capitalize(), "#0F7CFF")}---<br>{HELP_TEXT[command]}<br>'
    elif command == 'manual':
        return '@manual'
    else:
        s1 = 'To learn about units try these commands:<br>'
        s2 = f'{paint("help", "#4BDC28")}<br>     {paint("<br>     ".join(UNITS), "#4BDC28")}<br>'
        s3 = f'To read the general rules type<br>{paint("help rules", "#4BDC28")}<br>'
        s4 = f'To open the whole manual type<br>{paint("help manual", "#4BDC28")}<br>'
        return s1 + s2 + s3 + s4
