import json
from types import SimpleNamespace
from typing import List, Tuple
from exceptions import *
from utils import *
import re
from copy import deepcopy
from command_handler import CommandHandler


class Unit:
    def __init__(self, id, pos, TYPE, IN_GROUP=None,
                 IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=False,
                 IS_COUPLED=False, IS_CONTAINER=False):
        self.id = id
        self.pos = pos
        self.TYPE = TYPE
        self.IN_GROUP = IN_GROUP
        self.IS_MOVABLE = IS_MOVABLE
        self.IS_STACKABLE = IS_STACKABLE
        self.IS_CONTROLLABLE = IS_CONTROLLABLE
        self.IS_COUPLED = IS_COUPLED
        self.IS_CONTAINER = IS_CONTAINER

    def destroy(self):
        # replaces itself with None object
        pass

    def describe(self):
        return f'id={self.id} group_id={self.IN_GROUP} pos={self.pos} type={self.TYPE} controllable={self.IS_CONTROLLABLE} object={self}'


class Container(Unit):
    def __init__(self, id, pos, TYPE, holds=None, IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=True):
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
    def __init__(self, id, pos, COUPLE_ID, TYPE, holds=None, IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=True, IS_CONTAINER=True):
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
                if isinstance(self.contents, Container):
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
        self.NOTE = []
        self.create_empty_field()
        self.load_objects_from_txt(level_file)
        self.fill_field()
        self.active = True
        self.command_handler = CommandHandler()
        # self.INITIAL_CONFIGS = {
        #     'FIELD': deepcopy(self.field),
        #     'OBJECTS': deepcopy(self.objects)
        # }
        self.command_history = []
        
        with open('options.json') as f:
            self.OPTIONS = json.load(f)

    

    def is_victory(self):
        return ''.join(self.submitted) in self.WORDS

    def reset_game(self):
        self.field = deepcopy(self.INITIAL_CONFIGS['FIELD'])
        self.objects = deepcopy(self.INITIAL_CONFIGS['OBJECTS'])
        self.command_history = []

    def create_empty_field(self):
        # TODO: edit board_size 8x12 -> 6x10
        self.field: List[List[Cell]] = [[Cell(pos=(i, j)) for j in range(BOARD_SIZE[1])]
                                        for i in range(BOARD_SIZE[0])]

    def load_objects_from_txt(self, instruction_file):
        patterns = {
            'unit': re.compile(r'^(\d \d) (\w+)( .+)?'),
            'groups': re.compile(r'^groups: ?\{([\[\] ,\d]+)\}'),
            'words': re.compile(r'^words: ?\{([A-Z .]+)\}'),
            'letters': re.compile(r'^letters: ?\{([A-Z.]+)\}'),
            'note': re.compile(r'^# ?(.*)')
        }
        pattern_integer_value = re.compile(r'(\w+)=(\w+)')
        pattern_str_value = re.compile(r"(\w+)='(\w+)'")
        unit_classes = {
            'Manipulator': Manipulator,
            'ConveyorBelt': ConveyorBelt,
            'Stack': Stack,
            'Rock': Rock,
            'Flipper': Flipper,
            'Portal': Portal
        }
        group_id = 0
        unit_id = 0
        with open(instruction_file) as f:
            lines = f.readlines()

        for line in lines:
            for name, pattern in patterns.items():
                if pattern.match(line):
                    search_groups = pattern.search(line).groups()
                    if name == 'unit':
                        position_str, unit_name, kwargs_str = search_groups
                        pos = tuple(map(int, position_str.split()))
                        if kwargs_str is None:
                            kwargs = dict()
                        else:
                            kwargs_list = kwargs_str.strip().split()
                            kwargs = dict()
                            for kw in kwargs_list:
                                if pattern_integer_value.match(kw):
                                    key_, val_ = pattern_integer_value.search(
                                        kw).groups()
                                    kwargs[key_] = int(val_)
                                elif pattern_str_value.match(kw):
                                    key_, val_ = pattern_str_value.search(
                                        kw).groups()
                                    kwargs[key_] = val_
                        if unit_name == 'InitStack':
                            self.objects.append(
                                InitStack(id=unit_id, pos=pos, letters=self.LETTERS))
                        elif unit_name == 'Submitter':
                            self.objects.append(
                                Submitter(id=unit_id, pos=pos, submitted=self.submitted))
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
                                raise GroupOfDifferentTypes
                            group_id += 1
                    elif name == 'words':
                        self.WORDS = search_groups[0].split()
                    elif name == 'letters':
                        self.LETTERS = search_groups[0]
                    elif name == 'note':
                        self.NOTE.append(search_groups[0])
                    else:
                        raise UnmatchedCreationPattern
        # coupled objects:
        for obj in self.objects:
            if isinstance(obj, Coupled):
                obj.COUPLE = self.objects[obj.COUPLE_ID]
        # other groups
        for id, unit in enumerate(self.objects):
            if unit.TYPE in CONTROLLABLE_UNITS and unit.IN_GROUP is None:
                self.groups.append(
                    Group(id=group_id, units_type=unit.TYPE, units=[id])
                )
                self.objects[id].IN_GROUP = group_id
                group_id += 1

    def fill_field(self):
        for obj in self.objects:
            pos = obj.pos
            self.field[pos[0]][pos[1]].contents = obj

    def terminate(self, message):
        self.terminated = True
        print(message)

    def execute(self, obj: Unit, command):
        if obj.pos is None:
            raise ControllableIsInsideContainer
        if obj.TYPE == 'manipulator':
            if command == 't':
                obj.c_take(game=self)
            elif command == 'p':
                obj.c_put(game=self)
            elif command == 'c':
                obj.c_rotate_clockwise()
            elif command == 'r':
                obj.c_rotate_counter_clockwise()
            else:
                raise UnknownCommand(
                    f'Unknown command for {obj.TYPE}: {command}')
        elif obj.TYPE == 'piston':
            pass
        elif obj.TYPE == 'conveyorbelt':
            if command == '+':
                obj.c_shift_positive(game=self)
            elif command == '-':
                obj.c_shift_negative(game=self)
            else:
                raise UnknownCommand(
                    f'Unknown command for {obj.TYPE}: {command}')
        elif obj.TYPE == 'flipper':
            if command == 'f':
                obj.flip_unit(game=self)
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
    def __init__(self, id, pos, letter, TYPE='card', IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=False):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE, IS_STACKABLE,
                         IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.letter = letter

    def __str__(self):
        return f"'{self.letter}'"


class Manipulator(Unit):
    def __init__(self, id, pos, direction=0, holds=None, TYPE='manipulator', IN_GROUP=None, IS_MOVABLE=True,
                 IS_STACKABLE=True, IS_CONTROLLABLE=True, IS_COUPLED=False, IS_CONTAINER=False):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.direction = direction
        self.holds = holds

    def __str__(self):
        return f'M{self.direction}[{self.holds if self.holds is not None else ""}]'

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
    def __init__(self, id, pos, orientation='h', TYPE='conveyorbelt', IN_GROUP=None, holds=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=True, IS_COUPLED=False, IS_CONTAINER=True):
        super().__init__(id, pos, TYPE, IN_GROUP, holds, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.orientation = orientation

    def __str__(self):
        return f'C{self.orientation}[{self.holds if self.holds is not None else ""}]'

    def c_shift_positive(self, game: Game):
        if self.orientation == 'h':
            delta = DIRECTIONS[1]  # right
        else:
            delta = DIRECTIONS[2]

        position = (self.pos[0] + delta[0],
                    self.pos[1] + delta[1])

        if inside_borders(position):
            if not self.is_empty():
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

        if inside_borders(position):
            if not self.is_empty():
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


class Portal(Coupled):
    def __init__(self, id, pos, COUPLE_ID, TYPE='portal', holds=None, IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=True, IS_CONTAINER=True):
        super().__init__(id, pos, COUPLE_ID, TYPE, holds, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)

    def put_object(self, obj: Unit):
        self.send(obj)

    def send(self, obj):
        if self.COUPLE.is_empty():
            self.COUPLE.holds = obj
            self.holds = None
        else:
            raise OccupiedPortal('That portal is occupied')

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
        return f'S[{s}]'


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
        return f'{"{"}{s}{"}"}'


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
            raise NotCardSubmitted

    def is_empty(self):
        return not bool(self.submitted)

    def __str__(self):
        s = ''.join(self.submitted)
        return f'|{s}|'


class Flipper(Unit):
    def __init__(self, id, pos, direction, TYPE='flipper', IN_GROUP=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=True, IS_COUPLED=False, IS_CONTAINER=False):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.direction = direction

    def flip_unit(self, game):
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
        return f'F{self.direction}'


class Rock(Unit):
    def __init__(self, id, pos, TYPE='rock', IN_GROUP=None, IS_MOVABLE=False, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=False):
        super().__init__(id, pos, TYPE, IN_GROUP, IS_MOVABLE, IS_STACKABLE,
                         IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)

    def __str__(self):
        return 'Rock'


# if __name__ == '__main__':
#     g = Game('level_files/level2.txt')
#     print(g.WORDS, g.LETTERS)
#     for i, el in enumerate(g.objects):
#         print(el, el.IN_GROUP)
#     print(g.groups)
