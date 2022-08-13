from typing import List
from exceptions import *
from utils import *
import re


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
        else:
            raise OccupiedContainer


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
                raise OccupiedCell
            if isinstance(self.contents, Container):
                self.contents.put_object(self.pending)
                self.pending = None
                # TODO: need to clear pending
            self.contents.pos = self.pos

    def take(self):
        if self.contents is None:
            raise EmptyCell
        if isinstance(self.contents, Container) and not self.contents.is_empty():
            return self.contents.get_object()
        if self.contents.IS_MOVABLE:
            tmp = self.contents
            self.contents = None
            return tmp
        else:
            raise ImmovableUnit

    def put(self, obj):
        self.pending = obj


class Game:
    def __init__(self, WORDS) -> None:
        self.WORDS = WORDS
        self.objects = []
        self.groups = []
        self.create_empty_field()
        self.load_dummy_objects()
        self.create_dummy_groups()
        self.fill_field()
        self.commands = None
        self.terminated = False

    def create_empty_field(self):
        # loading field from .txt file
        self.field: List[List[Cell]] = [[Cell(pos=(i, j)) for j in range(12)]
                                        for i in range(8)]

    def load_objects_from_txt(self, instruction):
        pattern = re.compile(r'^(\d \d) (\w+)( .+)?')
        with open(instruction) as f:
            lines = f.readlines()
        for line in lines:
            print(pattern.search(line).groups())

    def load_dummy_objects(self):
        self.objects = [
            Manipulator(0, (1, 0), 1),
            ConveyorBelt(1, (1, 1)),
            ConveyorBelt(2, (1, 2)),
            Manipulator(3, (2, 2), 3),
            Manipulator(4, (0, 0), 3),
            Rock(5, (2, 3))
        ]

    def create_dummy_groups(self):
        self.groups = [
            Group(id=0, units_type='conveyorbelt', units=[
                  self.objects[1], self.objects[2]]),
            Group(id=1, units_type='manipulator', units=[self.objects[0]]),
            Group(id=2, units_type='manipulator', units=[self.objects[3]]),
            Group(id=3, units_type='manipulator', units=[self.objects[4]]),
        ]

    def fill_field(self):
        for obj in self.objects:
            pos = obj.pos
            self.field[pos[0]][pos[1]].contents = obj

    def terminate(self, message):
        self.terminated = True
        print(message)

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

    def execute_on_group(self, group_id: int, command: str):
        # TODO: special cases
        for obj in self.groups[group_id].units:
            self.execute(obj, command)
        self.push_all()

    def push_all(self):
        for i in range(8):
            for j in range(12):
                self.field[i][j].push()


class Group:
    def __init__(self, id, units_type, units, IS_COUPLED=False):
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

    def __str__(self):
        return f'{self.id}M{self.direction}[{self.holds}]'

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

        position = (self.pos[0] + DIRECTIONS[self.direction][0],
                    self.pos[1] + DIRECTIONS[self.direction][1])
        print('Hand over position:', position)
        if inside_borders(position):
            try:
                print('Trying to take', game.field[position[0]][position[1]])
                self.holds = game.field[position[0]][position[1]].take()
            except EmptyCell:
                game.terminate('Manipulator cannot take from an empty cell')
                return
        else:
            game.terminate('Outside of the borders')

    def c_put(self, game: Game):
        if self.holds is None:
            game.terminate(
                'There is nothing to put: manipulator\'s hand is empty')
            return

        position = (self.pos[0] + DIRECTIONS[self.direction][0],
                    self.pos[1] + DIRECTIONS[self.direction][1])
        if inside_borders(position):
            game.field[position[0]][position[1]].put(self.holds)
            self.holds = None
        else:
            game.terminate('Outside of the borders')


class ConveyorBelt(Container):
    def __init__(self, id, pos, orientation='h', TYPE='conveyorbelt', holds=None, IS_MOVABLE=True, IS_STACKABLE=True, IS_CONTROLLABLE=True, IS_COUPLED=False, IS_CONTAINER=True):
        super().__init__(id, pos, TYPE, holds, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.orientation = orientation

    def __str__(self):
        return f'{self.id}C{self.orientation}[{self.holds}]'

    def c_shift_positive(self, game: Game):
        pass

    def c_shift_negative(self, game: Game):
        pass


class Stack(Container):
    def __init__(self, id, pos, stack=None, TYPE='stack', holds=None, IS_MOVABLE=True, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=True):
        super().__init__(id, pos, TYPE, holds, IS_MOVABLE,
                         IS_STACKABLE, IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)
        self.stack = [] if stack is None else stack

    def append(self, obj):
        self.stack.append(obj)

    def __str__(self):
        return 'S'


class Rock(Unit):
    def __init__(self, id, pos, TYPE='rock', IS_MOVABLE=False, IS_STACKABLE=False, IS_CONTROLLABLE=False, IS_COUPLED=False, IS_CONTAINER=False):
        super().__init__(id, pos, TYPE, IS_MOVABLE, IS_STACKABLE,
                         IS_CONTROLLABLE, IS_COUPLED, IS_CONTAINER)

    def __str__(self):
        return 'R'


if __name__ == '__main__':
    g = Game([])
    g.load_objects_from_txt('level.txt')
