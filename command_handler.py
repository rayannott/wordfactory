from types import SimpleNamespace
from exceptions import CommandSyntaxError, EmptyPrompt, NotASingleCommand, UnmatchedParentheses, IncorrectLoopSyntax, IncorrectReferencesSyntax
import re


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
        self.pattern_loops = re.compile(r'(\d+)\[([^\[\]]+)\]')
        self.pattern_references = re.compile(r'#(\d+)')
        self.pattern_cmds = re.compile(r'(\d+)([a-z+-])$')

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

    def simple_command_sequence(self, raw_text):
        '''
        "result" for raw_text without loops and groups
        '''
        result = []
        for raw_command in raw_text.split():
            result.extend(self.commands_on_single_group(raw_command))
        return result

    def get_command_sequence(self, raw_text):
        if not raw_text:
            raise EmptyPrompt('There is nothing to execute')
        if not CommandHandler.valid_parentheses(raw_text):
            raise UnmatchedParentheses(
                'Some parentheses are unmatched in the command')
        if not set('[]()').intersection(set(raw_text)):
            res = self.simple_command_sequence(raw_text)
            return res, list(map(lambda x: f'{x[0]}{x[1]}', res))
        
        result = []
        loops = self.find_loops(raw_text)
        individual_commands = self.find_commands_on_single_groups(raw_text)
        merged = loops + individual_commands
        merged.sort(key=lambda x: x.span[0])
        for m in merged:
            if m.type == 'cmd':
                result.extend(self.simple_command_sequence(m.cmd))
            elif m.type == 'loop':
                result.extend(self.simple_command_sequence(
                    m.body) * m.iterations)
        result_to_display = list(
            map(lambda x: f'{x[0]}{x[1]}', result))
        return result, result_to_display

    def find_loops(self, text):
        loops = []  # (span, iterations, body)
        self.loop_spans = []
        for loop in self.pattern_loops.finditer(text):
            iterations, body = loop.groups()
            loops.append(SimpleNamespace(
                type='loop', span=loop.span(), iterations=int(iterations), body=body))
            self.loop_spans.append(loop.span())
        return loops

    # def find_groups(self, text):
    #     self.groups = []
    #     for el in self.pattern_groups.finditer(text):
    #         print('group', el)

    # def find_references(self, text):
    #     for el in self.pattern_references.finditer(text):
    #         print('ref', el)

    def find_commands_on_single_groups(self, text):
        # finds commands outside of loops
        ind_commands = []  # (span, (group_id, cmd_char))
        for cmd in self.pattern_commands_on_single_group.finditer(text):
            if not any((CommandHandler.is_subsector(cmd.span(), loop_span) for loop_span in self.loop_spans)):
                ind_commands.append(SimpleNamespace(
                    type='cmd', span=cmd.span(), cmd=cmd.group()))
        return ind_commands

    @staticmethod
    def is_subsector(sector1, sector2):
        return sector2[0] < sector1[0] and sector1[1] < sector2[1]


if __name__ == '__main__':
    ch = CommandHandler()
    # text = '1t 2[1c] 1ef 2[3rr 2qc 1c] 1tq 4f'
    # ch.find_loops(text)
    text = '1trev 3g 45fd'
    # print(ch.find_loops(text))
    # print(ch.find_commands_on_single_groups(text))
    # print(CommandHandler.is_subsector((1, 4), (3, 8)))
    print(ch.get_command_sequence(text))
