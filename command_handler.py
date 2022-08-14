from imaplib import Commands
from exceptions import CommandSyntaxError, EmptyPrompt, UnmatchedParentheses, IncorrectLoopSyntax, IncorrectReferencesSyntax, GroupInsideLoop
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
        self.pattern_commands_on_single_group = re.compile(r'(\d+)([a-z+-]+)')
        self.pattern_groups = re.compile(r'\(([^\(\)]+)\)')
        self.pattern_loops = re.compile(r'(\d+)\[([^\[\]]+)\]')
        self.pattern_references = re.compile(r'#(\d+)')
        self.pattern_cmds = re.compile(r'(\d+)([trc+p])')
        self.reset()

    def reset(self):
        self.result_to_display = []
        self.result = []

    def commands_on_single_group(self, raw_text):
        if not raw_text:
            raise EmptyPrompt('There is nothing to execute')
        try:
            group_id_str, cmd_char = self.pattern_commands_on_single_group.search(
                raw_text).groups()
        except:
            raise CommandSyntaxError(f'Syntax error: {raw_text}')
        group_id = int(group_id_str)
        return [(group_id, char) for char in cmd_char]

    def get_command_sequence(self, raw_text):
        if not raw_text:
            raise EmptyPrompt('There is nothing to execute')
        if not set('[]()').intersection(set(raw_text)):
            print('no loops and groups!')
            for raw_command in raw_text.split():
                self.result.extend(self.commands_on_single_group(raw_command))
            print(self.result)
            self.result_to_display = list(
                map(lambda x: f'{x[0]}{x[1]}', self.result))
        if not CommandHandler.valid_parentheses(raw_text):
            raise UnmatchedParentheses(
                'Some parentheses are unmatched in the command')
        # if re.findall(r'\[[^\[\]]*[\(\)][^\[\]]*\]', raw_text):
        #     raise GroupInsideLoop('You cannot create a group inside of a loop')
        # if '[' in raw_text and re.findall(r'[^\d]\[', raw_text):
        #     raise IncorrectLoopSyntax('Loop syntax is incorrect')
        # if '#' in raw_text and re.findall(r'#[^\d]', raw_text):
        #     raise IncorrectReferencesSyntax('Reference syntax is incorrect')
        # self.find_groups(raw_text)
        # self.find_individual_commands(raw_text)
        # self.find_loops(raw_text)
        # self.find_references(raw_text)

    def find_loops(self, text):
        for el in self.pattern_loops.finditer(text):
            print('loop', el)

    def find_groups(self, text):
        self.groups = []
        for el in self.pattern_groups.finditer(text):
            print('group', el)

    def find_references(self, text):
        for el in self.pattern_references.finditer(text):
            print('ref', el)

    def find_individual_commands(self, text):
        for el in self.pattern_cmds.finditer(text):
            print('cmd', el)


if __name__ == '__main__':
    ch = CommandHandler()
    text = '1t (3+ 1p) 1c (1e) 5[3r #2 1c] #1'
    ch.get_command_sequence(text)
