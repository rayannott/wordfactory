class CustomException(Exception):
    pass


class Warning(CustomException):
    pass

class CommandWarning(Warning):
    pass


class CommandException(CustomException):
    pass

# ........

class NonExistingGroup(Warning):
    pass

class ImmovableUnit(Warning):
    pass


class EmptyHand(Warning):
    pass


class TakingFromEmptyCell(Warning):
    pass


class TakingFromOusideOfField(Warning):
    pass


class HandNotEmpty(Warning):
    pass


class FlippingOusideOfField(Warning):
    pass


class NothingToFlip(Warning):
    pass


class ObjectUnflippable(Warning):
    pass


class OccupiedContainer(CustomException):
    pass

class OccupiedPortal(CustomException):
    pass

class OccupiedCell(CustomException):
    pass


class EmptyCell(CustomException):
    pass


class ControllableIsInsideContainer(CustomException):
    pass


class OutsideOfField(CustomException):
    pass


class UnknownCommand(CustomException):
    pass


class StackOverflow(CustomException):
    pass


class InitStackPutObject(CustomException):
    pass


class SubmitterTakeObject(CustomException):
    pass


class InitStackFlip(CustomException):
    pass


class ObjectNotStackable(CustomException):
    pass


class NotCardSubmitted(CustomException):
    pass


class PutOutsideOfField(CustomException):
    pass

# ...


class LevelCreationError(CustomException):
    pass


class UnmatchedCreationPattern(LevelCreationError):
    pass


class GroupOfDifferentTypes(LevelCreationError):
    pass


# ...


class UnmatchedParentheses(CommandWarning):
    pass

class CommandSyntaxError(CommandWarning):
    pass

class IncorrectLoopSyntax(CommandSyntaxError):
    pass


class IncorrectReferencesSyntax(CommandSyntaxError):
    pass


# class GroupInsideLoop(CommandWarning):
#     pass


class EmptyPrompt(CommandWarning):
    pass


class UnknownCommand(CommandWarning):
    pass


class NotASingleCommand(CommandWarning):
    pass