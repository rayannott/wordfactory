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


def load_level_filenames():
    def key(file):
        try:
            return int(file[5:-4])
        except ValueError:
            return -1
    import os
    level_files = os.listdir('level_files')

    result = [el for el in level_files if el.startswith(
        'level') and el.endswith('.txt')]
    result.sort(key=key)
    return result


HELP_TEXT = {
    'rules': 'Move Cards to the Submitter in correct order by giving commands to controllable units',
    'card':  'A unit with a letter (or a period) on it. They need to be submitted to the Submitter in an order so that one of the words is created.',
    'initstack': 'An immovable unit in which usually the letter Cards are stored. You can take from it but cannot put back.',
    'submitter': 'Put Cards here',

    'manipulator': 'Main force of your factory. It can move units by taking them from adjacent cells. Rotate its hand to choose where to place whatever the manipulator is holding.<br>' +
    paint('commands:<br>', '#ADE21E') + f'{paint("t", "#ADE21E")} -- take a movable unit from the cell in direction it is facing<br>' + f'{paint("p", "#ADE21E")} -- put a unit it is holding to the cell in direction it is facing<br>' +
    f'{paint("c", "#ADE21E")} -- rotate hand clockwise 90 degrees<br>' +
    f'{paint("r", "#ADE21E")} -- rotate hand anti-clockwise 90 degrees<br>',

    'conveyorbelt': '',

    'flipper': '',

    'piston': '',

    'rock': '',
    'portal': '',
    'stack': '',
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
