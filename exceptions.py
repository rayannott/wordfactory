class OccupiedContainer(Exception):
    pass

class OccupiedCell(Exception):
    pass

class EmptyCell(Exception):
    pass

class ImmovableUnit(Exception):
    pass

class OutsideOfField(Exception):
    pass


class UnknownCommand(Exception):
    pass


class EmptyHand(Exception):
    pass

# ...


class CommandException(Exception):
    pass


class UnmatchedParentheses(CommandException):
    pass


class IncorrectLoopSyntax(CommandException):
    pass

class IncorrectReferencesSyntax(CommandException):
    pass

class GroupInsideLoop(CommandException):
    pass
