import re
import json

DIRECTIONS = {
    0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)
    # up right down left
}
FRAMERATE = 30
WINDOW_SIZE = (1200, 800)
CELL_SIZE = (100, 100)
MARGIN = 3
BOARD_SIZE = (6, 8)
LEVELS_GRID_SIZE = (7, 9)
GROUP_ID_TEXTBOX_SIZE = (30, 28)
COMMAND_INPUT_FORBIDDEN_CHARS = list('/')
COMMAND_INPUT_HEIGHT = 40
MUSIC_DEFAULT_VOLUME = 0.25
SFX_DEFAULT_VOLUME = 0.4
LEVELS_DIR = 'levels'
SFX_DIR = 'assets/SFX'
SAVES_FILE_PATH = 'assets/save/save.json'
UNITS = {'manipulator', 'portal', 'conveyorbelt', 'rock', 'initstack', 'stack', 'flipper',
         'submitter', 'card', 'piston', 'anvil', 'typo'}
CONTROLLABLE_UNITS = {'manipulator', 'conveyorbelt', 'flipper', 'piston'}


def inside_borders(pos):
    row, col = pos
    return 0 <= row < BOARD_SIZE[0] and 0 <= col < BOARD_SIZE[1]

def shift(vec1: tuple[int, int], vec2: tuple[int, int]) -> tuple[int, int]:
    return (vec1[0] + vec2[0], vec1[1] + vec2[1])


def paint(s: str, color: str = '#FFFFFF', size=4):
    '''
    Returns html-colored with given color string s
    '''
    return f'<font color={color} size={size}>{s}</font>'

def paint_linear(text, number: float, rang: tuple[float, float], color_range) -> str:
    t = (number - rang[0])/(rang[1] - rang[0])
    color_tuple = (
        int(color_range[0][0]*(1-t)+color_range[1][0]*t),
        int(color_range[0][1]*(1-t)+color_range[1][1]*t),
        int(color_range[0][2]*(1-t)+color_range[1][2]*t)
    )
    return paint(text, '#%02x%02x%02x' % color_tuple)


def get_level_number_from_filename(filename):
    _, level_number = re.compile(
        f'({LEVELS_DIR}/)?level(.+).txt').search(filename).groups()
    return level_number



def load_level_filenames():
    def key(file):
        match = level_filename_pattern.match(file)
        if not match:
            return 10000
        lvl_num, _, sub_lvl_num = match.groups()
        if sub_lvl_num:
            return int(lvl_num) + int(sub_lvl_num)/1000
        return int(lvl_num)
    
    import os
    level_files = os.listdir(LEVELS_DIR)

    level_filename_pattern = re.compile(r'level(\d+)(\.(\d+))?.txt')
    result = [el for el in level_files if el.startswith('level') and el.endswith('.txt')]
    result.sort(key=key)
    return result


HELP_TEXT = {
    'rules': 'Move Cards to the Submitter in correct order by giving commands to controllable units; the goal is to create one of the words from inside of the curly braces shown after the level number.<br>' +
    'Controllable units are placed into controllable groups which have a unique id (shown in the cells\' top right corner); commands are given to those groups and executed by all units inside of them simultaneously.<br>' + 
    paint('Controls', '#62AAF7') + ':<br>-to execute a single command ([group_id][command_character]) press Return;<br>-to compile a sequence of commands* press Shift+Return, then press Return to execute selected command (press Esc to exit this mode) or Ctrl+Return to let it slowly go through the remaining commands;<br>' + 
    '-to execute a sequence of commands instantly press Ctrl+Shift+Return.<br>',

    'card':
    'A unit with a letter (or a period) on it. Needs to be submitted to the Submitter in such an order that one of the words is created.',

    'initstack':
    'An immovable unit in which usually the letter Cards are stored. You can take from it but cannot put back.',

    'submitter':
    'Put Cards here. Beware: what has been submitted cannot be taken back!',

    'manipulator':
    '[controllable]<br>Main force of your factory. It can move units by taking them from adjacent cells.<br>Rotate its hand to choose where to place whatever the manipulator is holding.<br>' +
    paint('commands:<br>', '#ADE21E') +
    f'{paint("t", "#ADE21E")} -- take a movable unit from the cell in the direction it is facing<br>' +
    f'{paint("p", "#ADE21E")} -- put a unit it is holding to the cell in the direction it is facing<br>' +
    f'{paint("c", "#ADE21E")} -- rotate hand clockwise 90 degrees<br>' +
    f'{paint("a", "#ADE21E")} -- rotate hand anti-clockwise 90 degrees'+
    f'{paint("s", "#ADE21E")} -- rotate hand 180 degrees',


    'conveyorbelt':
    '[controllable]<br>Another controllable unit which is also a container (one can put on or take from it). A conveyorbelt is oriented horisontally or vertically.<br>' +
    paint('commands:<br>', '#ADE21E') +
    f'{paint("+", "#ADE21E")} -- push a unit off of itself in the positive direction (right, down)<br>' +
    f'{paint("-", "#ADE21E")} -- push a unit off of itself in the negative direction (left, up)',

    'flipper':
    '[controllable]<br>A unit that can flip other units.<br>' +
    paint('commands:<br>', '#ADE21E') +
    f'{paint("f", "#ADE21E")} -- if possible, flip a unit in front of it (in the direction it is facing)<br>' +
    'Flippable units include: conveyorbelt (changes orientation), piston, flipper, portal (switches off so that it can no longer teleport a unit away from it).',

    # TODO: add typo to flipper's manual

    'piston':
    '[controllable]<br>A unit that can push other units.<br>' +
    paint('commands:<br>', '#ADE21E') +
    f'{paint("x", "#ADE21E")} -- extend pushing a unit in front of it to the next cell in that exact direction<br>' +
    'Pistons can push containers (stacks, conveyorbelts, portals).',

    'portal':
    'A unit that has a pair - other portal unit bound to it. If placed on an active portal, units are teleported to the portal\'s counterpart if it is not occupied.',

    'stack':
    'A container that can hold multiple items. Imitates a functionality of a stack data structure.<br>' +
    'Stacks cannot be put inside of other stacks.',

    'anvil':
    'Anvil is a unit that crushes (deletes from the field) any unit it is placed on. Anvils cannot crush Submitters.<br>' +
    'Crushing a portal with an anvil deactivates portal\'s counterpart. Crushing a typo with an anvil deactivates the typo.',

    'rock': 'A unit which cannot be pushed or moved.',

    'typo':
    'Shit', 
    # TODO: change this shit to something reasonable
}


def help_commands_processing(raw_command: str):
    command = raw_command[5:].strip()
    if command in HELP_TEXT:
        return f'----{paint(command.capitalize(), "#0F7CFF")}----<br>{HELP_TEXT[command]}<br>'
    elif command == 'manual':
        return '@manual'
    else:
        s1 = 'To learn about units try these commands:<br>'
        s2 = f'{paint("-help", "#4BDC28")}<br>     {paint("<br>     ".join(UNITS), "#4BDC28")}<br>'
        s3 = f'To read the general rules type<br>{paint("-help rules", "#4BDC28")}<br>'
        s4 = f'To open the whole manual type<br>{paint("-help manual", "#4BDC28")}<br>'
        return s1 + s2 + s3 + s4

def load_progress_data():
    try:
        with open(SAVES_FILE_PATH, 'r') as f:
            saves = json.load(f)
    except FileNotFoundError:
        saves = dict()
    return saves

def save_progress_data(data_to_save):
    with open(SAVES_FILE_PATH, 'w') as f:
        json.dump(data_to_save, f)

def update_solution(progress_data_dict, filename, submitted_word, num_of_cmds, solution):
    this_word_to_save = {
        'num_of_cmds': num_of_cmds,
        'solution': solution
    }
    this_entry = progress_data_dict.get(filename)
    if this_entry:
        this_word = this_entry.get(submitted_word)
        if this_word and num_of_cmds <= this_word['num_of_cmds'] or not this_word: 
            this_entry[submitted_word] = this_word_to_save
            progress_data_dict[filename] = this_entry
    else:
        this_entry = {
            submitted_word: this_word_to_save
        }
        progress_data_dict[filename] = this_entry
    save_progress_data(progress_data_dict)

if __name__ == '__main__':
    pass