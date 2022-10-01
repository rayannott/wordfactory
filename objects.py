from types import SimpleNamespace
from typing import List, Tuple
from exceptions import *
from utils import *
import re
from copy import deepcopy
from command_handler import CommandHandler
from pygame import mixer
import os
from sfx import play_sfx


class Unit:
    def __init__(self, id, pos, TYPE, IN_GROUP=None,
                 IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=False,
                 IS_COUPLED=False, IS_CONTAINER=False, is_active=True):
        self.id = id
        self.pos = pos
        self.TYPE = TYPE
        self.IN_GROUP = IN_GROUP
        self.IS_MOVABLE = IS_MOVABLE
        self.IS_STACKABLE = IS_STACKABLE
        self.IS_CONTROLLABLE = IS_CONTROLLABLE
        self.IS_COUPLED = IS_COUPLED
        self.IS_CONTAINER = IS_CONTAINER
        self.is_active = is_active

    def describe(self):
        return f'id={self.id} group_id={self.IN_GROUP} pos={self.pos} type={self.TYPE} controllable={self.IS_CONTROLLABLE} is_active={self.is_active} object={self}'


class Container(Unit):
    def __init__(self, id, pos, TYPE, holds=None, IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=True, is_active=True):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.holds = holds

    def is_empty(self):
        return self.holds is None

    def get_object(self):
        if not self.is_empty():
            tmp = self.holds
            self.holds = None
            return tmp
        # if self.IS_MOVABLE:
        #     return self

    def put_object(self, obj: Unit):
        if self.is_empty():
            obj.pos = None
            self.holds = obj
        else:
            raise OccupiedContainer


class Coupled(Container):
    def __init__(self, id, pos, COUPLE_ID, TYPE, holds=None, IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=True, IS_CONTAINER=True, is_active=True):
        self.COUPLE_ID = COUPLE_ID
        self.COUPLE: Coupled = None
        super().__init__(id, pos, TYPE, holds, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)


class Cell:
    def __init__(self, pos, contents: Unit = None):
        self.pos = pos
        self.contents = contents
        self.pending = None

    def __str__(self):
        if self.contents is None:
            return ''
        return str(self.contents)

    def push(self):
        if self.pending is not None:
            if self.contents is None:
                self.contents = self.pending
                self.pending = None
            else:
                if isinstance(self.pending, Anvil):
                    # destroying units with an Anvil
                    if isinstance(self.contents, Submitter):
                        raise CrushingSubmitter('Nice try looser hahahahaah')
                    self.contents.is_active = False
                    if isinstance(self.contents, Portal):
                        self.contents.deactivate_couple()
                    if isinstance(self.contents, Typo):
                        self.contents.eliminate()
                    play_sfx('anvil')
                    self.contents = self.pending
                    self.pending = None
                elif isinstance(self.contents, Container):
                    self.contents.put_object(self.pending)
                    self.pending = None
                    # TODO: need to clear pending
                else:
                    raise OccupiedCell
            self.contents.pos = self.pos

    def take(self):
        if self.contents is None:
            raise EmptyCell
        if isinstance(self.contents, Container) and not self.contents.is_empty():
            return self.contents.get_object()
        if self.contents.IS_MOVABLE:
            # this means the object is inside of a container and cannot be controlled
            self.contents.pos = None
            tmp = self.contents
            self.contents = None
            return tmp
        else:
            raise ImmovableUnit(f'Unit {self.contents.TYPE} is immovable')

    def put(self, obj):
        self.pending = obj


class Game:
    def __init__(self, level_file: str):
        self.victory = False
        self.objects = []
        self.groups = []
        self.submitted = []
        self.typos = []
        self.number_of_commands = 0
        self.NOTE = []
        self.NAME = ''
        self.is_running = True


        self.create_empty_field()
        self.load_objects_from_txt(level_file)
        self.fill_field()
        self.active = True
        self.command_handler = CommandHandler()
        self.command_history = []

    def is_victory(self):
        return (''.join(self.submitted) in self.WORDS, all([typo.eliminated for typo in self.typos]))

    def create_empty_field(self):
        self.field: List[List[Cell]] = [[Cell(pos=(i, j)) for j in range(BOARD_SIZE[1])]
                                        for i in range(BOARD_SIZE[0])]

    def load_objects_from_txt(self, instruction_file):
        patterns = {
            'unit': re.compile(r'^(\d \d) (\w+)( .+)?'),
            'groups': re.compile(r'^groups?: ?\{([\[\] ,\d]+)\}'),
            'words': re.compile(r'^words?: ?\{([A-Z .]+)\}'),
            'letters': re.compile(r'^letters?: ?\{([A-Z.]+)\}'),
            'note': re.compile(r'^# ?(.*)'),
            'name': re.compile(r'^@ ?(.*)')
        }
        pattern_integer_value = re.compile(r'(\w+)=(\w+)')
        pattern_str_value = re.compile(r"(\w+)='(\w+)'")
        unit_classes = {
            'Manipulator': Manipulator,
            'ConveyorBelt': ConveyorBelt,
            'Stack': Stack,
            'Rock': Rock,
            'Flipper': Flipper,
            'Portal': Portal,
            'Card': Card,
            'Piston': Piston,
            'Anvil': Anvil,
            'Typo': Typo
        }
        group_id = 0
        unit_id = 0
        with open(instruction_file) as f:
            lines = f.readlines()
        # TODO: make portals set COUPLE_IDs automatically
        is_there_a_submitter = False
        are_words_specified = False
        for line in lines:
            for name, pattern in patterns.items():
                if pattern.match(line):
                    search_groups = pattern.search(line).groups()
                    if name == 'unit':
                        position_str, unit_name, kwargs_str = search_groups
                        pos = tuple(map(int, position_str.split()))
                        kwargs = dict()
                        if kwargs_str is not None:
                            kwargs_list = kwargs_str.strip().split()
                            for kw in kwargs_list:
                                if pattern_integer_value.match(kw):
                                    key_, val_ = pattern_integer_value.search(
                                        kw).groups()
                                    kwargs[key_] = int(val_)
                                elif pattern_str_value.match(kw):
                                    key_, val_ = pattern_str_value.search(
                                        kw).groups()
                                    kwargs[key_] = val_
                        # creating units
                        if unit_name == 'InitStack':
                            self.objects.append(
                                InitStack(id=unit_id, pos=pos, letters=self.LETTERS))
                        elif unit_name == 'Submitter':
                            self.objects.append(
                                Submitter(id=unit_id, pos=pos, submitted=self.submitted))
                            is_there_a_submitter = True
                        else:
                            self.objects.append(
                                unit_classes[unit_name](
                                    id=unit_id, pos=pos, **kwargs)
                            )
                        unit_id += 1
                    elif name == 'groups':
                        groups = search_groups[0].split(',')
                        for group in groups:
                            this_group_object_indices = list(
                                map(int, group.split()))
                            types_set = {
                                self.objects[i].TYPE for i in this_group_object_indices}
                            if len(types_set) == 1:
                                self.groups.append(
                                    Group(group_id, units_type=list(types_set)[
                                          0], units=this_group_object_indices)
                                )
                                for this_group_obj_index in this_group_object_indices:
                                    self.objects[this_group_obj_index].IN_GROUP = group_id
                            else:
                                raise GroupOfDifferentTypes(
                                    'There are groups containing units of different types')
                            group_id += 1
                    elif name == 'words':
                        self.WORDS = search_groups[0].split()
                        are_words_specified = True
                    elif name == 'letters':
                        self.LETTERS = search_groups[0]
                    elif name == 'note':
                        self.NOTE.append(search_groups[0])
                    elif name == 'name':
                        self.NAME = search_groups[0]
                    else:
                        raise UnmatchedCreationPattern(
                            'unmatched_creation_pattern??')
        if not is_there_a_submitter:
            raise SubmitterNotFound('There must be at least one submitter')
        if not are_words_specified:
            raise WordsNotSpecified('To create a level give a list of words')
        # coupled objects:
        for obj in self.objects:
            if isinstance(obj, Coupled):
                obj.COUPLE = self.objects[obj.COUPLE_ID]
        # individual groups
        for id, unit in enumerate(self.objects):
            if unit.TYPE in CONTROLLABLE_UNITS and unit.IN_GROUP is None:
                self.groups.append(
                    Group(id=group_id, units_type=unit.TYPE, units=[id])
                )
                self.objects[id].IN_GROUP = group_id
                group_id += 1
        # typos
        for obj in self.objects:
            if isinstance(obj, Typo):
                self.typos.append(obj)

    def fill_field(self):
        for obj in self.objects:
            pos = obj.pos
            self.field[pos[0]][pos[1]].contents = obj

    def execute(self, obj: Unit, command):
        if obj.pos is None:
            raise ControllableIsInsideContainer
        if obj.is_active:
            self.number_of_commands += 1
            if obj.TYPE == 'manipulator':
                if command == 't':
                    obj.c_take(game=self)
                    play_sfx('manipulator_p')
                elif command == 'p':
                    obj.c_put(game=self)
                    play_sfx('manipulator_p')
                elif command == 'c':
                    obj.c_rotate_clockwise()
                    play_sfx('manipulator_c')
                elif command == 'a':
                    obj.c_rotate_counter_clockwise()
                    play_sfx('manipulator_a')
                elif command == 's':
                    obj.c_rotate_clockwise()
                    obj.c_rotate_clockwise()
                    play_sfx('manipulator_a')
                else:
                    raise UnknownCommand(
                        f'Unknown command for {obj.TYPE}: {command}')
            elif obj.TYPE == 'piston':
                if command == 'x':
                    obj.c_extend(game=self)
                    play_sfx('piston')
                else:
                    raise UnknownCommand(
                        f'Unknown command for {obj.TYPE}: {command}')
            elif obj.TYPE == 'conveyorbelt':
                if command == '+':
                    obj.c_shift_positive(game=self)
                    play_sfx('conveyor')
                elif command == '-':
                    obj.c_shift_negative(game=self)
                    play_sfx('conveyor')
                else:
                    raise UnknownCommand(
                        f'Unknown command for {obj.TYPE}: {command}')
            elif obj.TYPE == 'flipper':
                if command == 'f':
                    obj.c_flip_unit(game=self)
                    play_sfx('flipper')
                else:
                    raise UnknownCommand(
                        f'Unknown command for {obj.TYPE}: {command}')
            elif obj.TYPE == 'swapper':
                pass

    # single_command_raw):
    def execute_on_group(self, single_command: Tuple[int, str]):
        # group_id, command = int(single_command_raw[0]), single_command_raw[1]
        group_id, command = single_command
        # TODO: special cases
        try:
            for obj_id in self.groups[group_id].units:
                self.execute(self.objects[obj_id], command)
        except IndexError:
            raise NonExistingGroup(f'There is no group with id={group_id}')
        self.push_all()

    def push_all(self):
        for i in range(BOARD_SIZE[0]):
            for j in range(BOARD_SIZE[1]):
                self.field[i][j].push()


class Group:
    def __init__(self, id, units_type, units, IS_COUPLED=False):
        self.id = id
        self.units_type = units_type
        self.units = units  # units' ids
        self.IS_COUPLED = IS_COUPLED


class Card(Unit):
    def __init__(self, id, pos, letter='.', TYPE='card', IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=False, is_active=True):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE, IS_STACKABLE,
                         IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.letter = letter

    def __str__(self):
        return f"{self.letter}"


class Manipulator(Unit):
    def __init__(self, id, pos, direction=0, holds=None, TYPE='manipulator', IN_GROUP=None, IS_MOVABLE=True,
                 IS_STACKABLE=True, IS_CONTROLLABLE=True, IS_COUPLED=False, IS_CONTAINER=False, is_active=True):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.direction = direction
        self.holds = holds

    def __str__(self):
        return f'M[{self.holds}]' if self.holds is not None else 'M'

    def c_rotate_clockwise(self):
        self.direction += 1
        self.direction %= 4

    def c_rotate_counter_clockwise(self):
        self.direction -= 1
        self.direction %= 4

    def c_take(self, game: Game):
        if self.holds is not None:
            raise HandNotEmpty('Cannot take: manipulator\'s hand is not empty')

        delta = DIRECTIONS[self.direction]
        position = (self.pos[0] + delta[0],
                    self.pos[1] + delta[1])
        if inside_borders(position):
            try:
                self.holds = game.field[position[0]][position[1]].take()
            except EmptyCell:
                raise TakingFromEmptyCell(
                    'Manipulator cannot take from an empty cell')
        else:
            raise TakingFromOusideOfField('Taking from outside of the borders')

    def c_put(self, game: Game):
        if self.holds is None:
            raise EmptyHand(
                'There is nothing to put: manipulator\'s hand is empty')

        delta = DIRECTIONS[self.direction]
        position = (self.pos[0] + delta[0],
                    self.pos[1] + delta[1])
        if inside_borders(position):
            game.field[position[0]][position[1]].put(self.holds)
            self.holds = None
        else:
            raise PutOutsideOfField(
                'Trying to put outside of the field borders')


class ConveyorBelt(Container):
    def __init__(self, id, pos, orientation='h', TYPE='conveyorbelt', IN_GROUP=None, holds=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=True, IS_COUPLED=False, IS_CONTAINER=True, is_active=True):
        super().__init__(id, pos, TYPE, IN_GROUP, holds, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.orientation = orientation

    def __str__(self):
        return f'C[{self.holds}]' if self.holds is not None else 'C'

    def c_shift_positive(self, game: Game):
        if self.orientation == 'h':
            delta = DIRECTIONS[1]  # right
        else:
            delta = DIRECTIONS[2]

        position = (self.pos[0] + delta[0],
                    self.pos[1] + delta[1])

        if not self.is_empty():
            if inside_borders(position):
                game.field[position[0]][position[1]].put(self.holds)
                self.holds = None
            else:
                raise PutOutsideOfField(
                    'Trying to put outside of the field borders')

    def c_shift_negative(self, game: Game):
        if self.orientation == 'h':
            delta = DIRECTIONS[3]  # right
        else:
            delta = DIRECTIONS[0]

        position = (self.pos[0] + delta[0],
                    self.pos[1] + delta[1])

        if not self.is_empty():
            if inside_borders(position):
                game.field[position[0]][position[1]].put(self.holds)
                self.holds = None
            else:
                raise PutOutsideOfField(
                    'Trying to put outside of the field borders')

    def flip(self):
        if self.orientation == 'h':
            self.orientation = 'v'
        else:
            self.orientation = 'h'


class Piston(Unit):
    def __init__(self, id, pos, direction, TYPE='piston', IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=True, IS_COUPLED=False, IS_CONTAINER=False, is_active=True):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.direction = direction

    def c_extend(self, game):
        delta = DIRECTIONS[self.direction]
        position_to_push = (self.pos[0] + delta[0],
                            self.pos[1] + delta[1])
        position_to_push_to = (self.pos[0] + 2*delta[0],
                               self.pos[1] + 2*delta[1])
        if inside_borders(position_to_push):
            if game.field[position_to_push[0]][position_to_push[1]].contents is not None:
                if game.field[position_to_push[0]][position_to_push[1]].contents.IS_MOVABLE:
                    if inside_borders(position_to_push_to):
                        game.field[position_to_push_to[0]][position_to_push_to[1]].put(
                            game.field[position_to_push[0]][position_to_push[1]].contents)
                        game.field[position_to_push[0]
                                   ][position_to_push[1]].contents = None
                    else:
                        raise PushingOutsideOfField(
                            'Pushing outside of the field is not allowed')
                else:
                    raise ImmovableUnit(
                        f'Unit {game.field[position_to_push[0]][position_to_push[1]].contents.TYPE} cannot be moved (pushed)')
        else:
            raise PushingFieldBorders('Nice try pushing the borders')

    def flip(self):
        self.direction += 1
        self.direction %= 4

    def __str__(self):
        return 'P'


class Portal(Coupled):
    def __init__(self, id, pos, COUPLE_ID, active=True, TYPE='portal', holds=None, IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=True, IS_CONTAINER=True):
        super().__init__(id, pos, COUPLE_ID, TYPE, holds, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.active = active

    def put_object(self, obj: Unit):
        if self.active:
            self.send(obj)
        else:
            super().put_object(obj)
        
    def deactivate_couple(self):
        self.COUPLE.active = False

    def send(self, obj):
        if self.COUPLE.pos == None:
            raise CoupledPortalInsideContainer
        if not self.COUPLE.is_empty():
            raise OccupiedPortal('That portal is occupied')
        obj.pos = None
        self.COUPLE.holds = obj
        self.holds = None
        play_sfx('portal_send')

    def flip(self):
        self.active = not self.active
        if not self.active:
            play_sfx('portal_off')

    def __str__(self):
        return f'{self.id}{self.COUPLE_ID}[{self.holds if self.holds is not None else ""}]'


class Stack(Container):
    def __init__(self, id, pos, stack=None, MAX_OBJECTS=20, TYPE='stack', holds=None, IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=True):
        super().__init__(id, pos, TYPE, holds, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.stack = [] if stack is None else stack
        self.MAX_OBJECTS = MAX_OBJECTS

    def is_empty(self):
        return not bool(self.stack)

    def get_object(self):
        if not self.is_empty():
            return self.stack.pop()
        return self

    def put_object(self, obj):
        if obj.IS_STACKABLE:
            if len(self.stack) < self.MAX_OBJECTS:
                self.stack.append(obj)
            else:
                raise StackOverflow
        else:
            raise ObjectNotStackable

    def flip(self):
        self.stack = self.stack[::-1]

    def __str__(self):
        s = ','.join(map(str, self.stack))
        return f'[{s}]'


class InitStack(Stack):
    def __init__(self, id, pos, letters, MAX_OBJECTS=20, TYPE='initstack', holds=None, IN_GROUP=None, IS_MOVABLE=False, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=True):
        stack = [Card(id=-i, pos=None, letter=ch)
                 for i, ch in enumerate(letters, 1)]
        super().__init__(id, pos, stack[::-1], MAX_OBJECTS, TYPE, holds, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)

    def put_object(self, obj):
        raise InitStackPutObject

    def flip(self):
        raise InitStackFlip

    def __str__(self):
        s = ''.join(map(lambda x: x.letter, self.stack))
        return f'{s}'


class Submitter(Container):
    def __init__(self, id, pos, submitted, TYPE='submitter', holds=None, IN_GROUP=None, IS_MOVABLE=False, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=True):
        super().__init__(id, pos, TYPE, holds, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.submitted = submitted

    def put_object(self, obj: Unit):
        self.submit(obj)

    def get_object(self):
        raise SubmitterTakeObject

    def submit(self, obj: Unit):
        if obj.TYPE == 'card':
            self.submitted.append(obj.letter)
        else:
            raise NotCardSubmitted(
                'Only Card units can be submitted to the Submitter')

    def is_empty(self):
        return not bool(self.submitted)

    def __str__(self):
        s = ''.join(self.submitted)
        return f'{s}'


class Flipper(Unit):
    def __init__(self, id, pos, direction, TYPE='flipper', IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=True, IS_COUPLED=False, IS_CONTAINER=False):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.direction = direction

    def c_flip_unit(self, game):
        delta = DIRECTIONS[self.direction]
        position = (self.pos[0] + delta[0],
                    self.pos[1] + delta[1])
        if inside_borders(position):
            if game.field[position[0]][position[1]].contents is not None:
                try:
                    game.field[position[0]][position[1]].contents.flip()
                except AttributeError:
                    raise ObjectUnflippable(
                        f'Object {game.field[position[0]][position[1]].contents.TYPE} is unflippable')
            else:
                raise NothingToFlip('There is nothing there to flip')
        else:
            raise FlippingOusideOfField(
                'Trying to flip an object outside of the field')

    def flip(self):
        self.direction += 1
        self.direction %= 4

    def __str__(self):
        return 'F'


class Rock(Unit):
    def __init__(self, id, pos, TYPE='rock', IN_GROUP=None, IS_MOVABLE=False, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=False):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE, IS_STACKABLE,
                         IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)

    def __str__(self):
        return ''


class Anvil(Unit):
    def __init__(self, id, pos, TYPE='anvil', IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=False):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)

    def __str__(self):
        return 'A'


class Typo(Unit):
    def __init__(self, id, pos, TYPE='typo', IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=False):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.eliminated = False

    def eliminate(self):
        self.eliminated = True
        play_sfx('one_typo_eliminated')

    def flip(self):
        self.eliminate()

    def __str__(self):
        return f'{":" if self.eliminated else "!"}'
