from exceptions import UnmatchedParentheses, IncorrectLoopSyntax, IncorrectReferencesSyntax, GroupInsideLoop
from utils import COMMAND_CHARACTERS
import re

'''
'1tcp 3+-' -> 1t 1c 1p 3+ 3- -> [(1, 't'), (1, 't'), (1, 'c'), (1, 'p'), (3, '+'), (3, '-')]
'3[2t]' -> 2t 2t 2t -> [(2, 't'), (2, 't'), (2, 't')]
'2[1+ 3tp] 1-' -> 1+ 3t 3p 1+ 3t 3p 1- -> ...
'1t (3+ 1p) 1c #1' -> 1t 3+ 1p 1c 3+ 1p -> ..
'(2t) 1- (2r 2c) 2[#1 1+ #2]' -> 2t 1- 2r 2c 2t 1+ 2r 2c 2t 1+ 2r 2c -> ...
'''

class CommandHandler:

    def valid_parentheses(s):
        stack = []
        parentheses = ['()', '[]']
        parentheses_set = {'(', ')', '[', ']'}
        open_close = {el[0]: el[1] for el in parentheses}
        for ch in s:
            if ch in parentheses_set:
                if ch in open_close:
                    stack.append(open_close[ch])
                else:
                    if not stack or ch != stack.pop():
                        return False
        return not stack

    def __init__(self):
        self.pattern_groups = re.compile(r'\(([^\(\)]+)\)')
        self.pattern_loops = re.compile(r'(\d+)\[([^\[\]]+)\]')
        self.pattern_references = re.compile(r'#(\d+)')
        self.pattern_cmds = re.compile(r'(\d+)([trc+p])')

        self.result = []


    def find_groups(self, text):
        self.groups = []
        for el in self.pattern_groups.finditer(text):
            print('group', el)
        

    def find_loops(self, text):
        for el in self.pattern_loops.finditer(text):
            print('loop', el)

    def find_references(self, text):
        for el in self.pattern_references.finditer(text):
            print('ref', el)

    def find_individual_commands(self, text):
        for el in self.pattern_cmds.finditer(text):
            print('cmd', el)

    def get_command_sequence(self, raw_text):

        if not CommandHandler.valid_parentheses(raw_text):
            raise UnmatchedParentheses('Some parentheses are unmatched in the command')
        if re.findall(r'\[[^\[\]]*[\(\)][^\[\]]*\]', raw_text):
            raise GroupInsideLoop('You cannot create a group inside of a loop')
        if '[' in raw_text and re.findall(r'[^\d]\[', raw_text):
            raise IncorrectLoopSyntax('Loop syntax is incorrect')
        if '#' in raw_text and re.findall(r'#[^\d]', raw_text):
            raise IncorrectReferencesSyntax('Reference syntax is incorrect')
        self.find_groups(raw_text)
        self.find_individual_commands(raw_text)
        self.find_loops(raw_text)
        self.find_references(raw_text)
        


if __name__ == '__main__':
    ch = CommandHandler()
    text = '1t (3+ 1p) 1c (1e) 5[3r 5p 1c] #1'
    ch.get_command_sequence(text)
        