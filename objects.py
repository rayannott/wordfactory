from typing import List
from exceptions import *
from utils import *


class Unit:
    def __init__(self, id, pos, TYPE,
                 IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=False,
                 IS_COUPLED=False, IS_CONTAINER=False):
        self.id = id
        self.pos = pos
        self.TYPE = TYPE
        self.IS_MOVABLE = IS_MOVABLE
        self.IS_STACKABLE = IS_STACKABLE
        self.IS_CONTROLLABLE = IS_CONTROLLABLE
        self.IS_COUPLED = IS_COUPLED
        self.IS_CONTAINER = IS_CONTAINER

    def destroy(self):
        # replaces itself with None object
        pass


class Container(Unit):
    def __init__(self, id, pos, TYPE, holds=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=True):
        super().__init__(id, pos, TYPE, IS_MOVABLE,
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

    def put_object(self, obj):
        if self.is_empty():
            self.holds = obj
        raise OccupiedContainer


class Cell:
    def __init__(self, contents: Unit = None):
        self.contents = contents
        self.pending = None

    def push(self):
        if self.pending is not None:
            if self.contents is None:
                self.contents = self.pending
                self.pending = None

            if isinstance(self.contents, Container):
                self.contents.put_object(self.pending)
                self.pending = None
                # TODO: need to clear pending

    def take(self):
        if self.contents is None:
            raise EmptyCell
        if isinstance(self.contents, Container):
            return self.contents.get_object()

    def put(self, obj):
        self.pending = obj


class Game:
    def create_field(self):
        self.field: List[List[Cell]] = [[Cell() for _ in range(
            self.BOARD_SIZE[1])] for _ in range(self.BOARD_SIZE[0])]

    def terminate(self, message):
        print(message)

    def __init__(self, WORDS, BOARD_SIZE) -> None:
        self.WORDS = WORDS
        self.BOARD_SIZE = BOARD_SIZE
        self.create_field()

    def execute(self, obj: Unit, command):
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
                self.terminate(f'Unknown command for {obj.TYPE}: {command}')
        elif obj.TYPE == 'piston':
            pass
        elif obj.TYPE == 'conveyorbelt':
            if command == '+':
                obj.c_shift_positive(game=self)
            elif command == '-':
                obj.c_shift_positive(game=self)
            else:
                self.terminate(f'Unknown command for {obj.TYPE}: {command}')
        elif obj.TYPE == 'flipper':
            pass
        elif obj.TYPE == 'swapper':
            pass

    def execute_command_on_group(self, group, command):
        # TODO: special cases
        for obj in group:
            self.execute(obj, command)


class Group:
    def __init__(self, id, units_type, units, IS_COUPLED):
        self.id = id
        self.units_type = units_type
        self.units = units
        self.IS_COUPLED = IS_COUPLED


class Manipulator(Unit):
    def __init__(self, id, pos, direction, holds=None, TYPE='manipulator', IS_MOVABLE=True,
                 IS_STACKABLE=True, IS_CONTROLLABLE=True, IS_COUPLED=False, IS_CONTAINER=False):
        super().__init__(id, pos, TYPE, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.direction = direction
        self.holds = holds

    def c_rotate_clockwise(self):
        self.direction += 1
        self.direction %= 4

    def c_rotate_counter_clockwise(self):
        self.direction -= 1
        self.direction %= 4

    def c_take(self, game: Game):
        if self.holds is not None:
            game.terminate('Cannot take: manipulator\'s hand is not empty')
            return
        board_size = game.BOARD_SIZE
        position = (self.pos[0] + DIRECTIONS[self.direction]
                    [0], self.pos[1] + DIRECTIONS[self.direction][1])
        if inside_borders(position, board_size):
            try:
                self.holds = game.field[position[0]][position[1]].take()
            except EmptyCell:
                game.terminate('Manipulator cannot take from an empty cell')
                return
        game.terminate('Outside of the borders')

    def c_put(self, game: Game):
        if self.holds is None:
            game.terminate(
                'There is nothing to put: manipulator\'s hand is empty')
            return
        board_size = game.BOARD_SIZE
        position = (self.pos[0] + DIRECTIONS[self.direction]
                    [0], self.pos[1] + DIRECTIONS[self.direction][1])
        if inside_borders(position, board_size):
            game.field[position[0]][position[1]].put(self.holds)
            self.holds = None
        game.terminate('Outside of the borders')


class ConveyorBelt(Container):
    def __init__(self, id, pos, orientation='h', TYPE='conveyorbelt', holds=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=True, IS_COUPLED=False, IS_CONTAINER=True):
        super().__init__(id, pos, TYPE, holds, IS_MOVABLE, IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.orientation = orientation
    
    def c_shift_positive(self, game : Game):
        pass
    
    def c_shift_negative(self, game : Game):
        pass
    

