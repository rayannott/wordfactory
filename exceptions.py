class Warning(Exception):
    pass

class EmptyHand(Warning):
    pass

class TakingFromEmptyCell(Warning):
    pass

class TakingFromOusideOfField(Warning):
    pass

class HandNotEmpty(Warning):
    pass

class OccupiedContainer(Exception):
    pass

class OccupiedCell(Exception):
    pass

class EmptyCell(Exception):
    pass

class ImmovableUnit(Exception):
    pass

class ControllableIsInsideContainer(Exception):
    pass

class OutsideOfField(Exception):
    pass


class UnknownCommand(Exception):
    pass


class StackOverflow(Exception):
    pass

class InitStackPutObject(Exception):
    pass


class ObjectNotStackable(Exception):
    pass

class NotCardSubmitted(Exception):
    pass

# ...

class UnmatchedCreationPattern(Exception):
    pass

class GroupOfDifferentTypes(Exception):
    pass

class PutOutsideOfField(Exception):
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
