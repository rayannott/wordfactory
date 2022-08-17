# from copy import deepcopy
from copy import deepcopy
import json
import re
from time import time
from types import SimpleNamespace
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIPanel, UITextEntryLine, UITextBox, UIWindow
from pygame_gui.elements.ui_drop_down_menu import UIDropDownMenu
from pygame_gui.windows import UIMessageWindow
from pygame_gui.core import ObjectID

from objects import Cell, Game
from exceptions import *
from utils import *


class UICell(UIButton):
    def __init__(self, relative_rect, cell: Cell, manager, OPTIONS, **kwargs):
        self.cell = cell
        self.text = str(cell)
        self.manager = manager
        self.OPTIONS = OPTIONS
        self.relative_rect = relative_rect
        self.kwargs = kwargs
        self.object_id = self.get_object_id()
        self.kwargs['object_id'] = self.object_id
        self.object_id_prev = self.object_id
        super().__init__(relative_rect, self.text, manager, **kwargs)
        rect_group_id = pygame.Rect(0, 0, 0, 0)
        rect_group_id.size = GROUP_ID_TEXTBOX_SIZE
        rect_group_id.topright = self.relative_rect.topright
        self.group_id_textbox = UITextBox(
            '', rect_group_id, self.manager, object_id=ObjectID(class_id='@Centered'))
        self.group_id_textbox.hide()

    def get_object_id(self):
        # TODO: draw flippers better
        this_unit = self.cell.contents
        if this_unit is not None:
            if this_unit.TYPE == 'manipulator':
                return f'#manipulator_{this_unit.direction}'
            elif this_unit.TYPE == 'conveyorbelt':
                return f'#conveyorbelt_{this_unit.orientation}'
            elif this_unit.TYPE == 'portal':
                return f'#portal_{"active" if this_unit.active else "inactive"}'
            elif this_unit.TYPE == 'flipper':
                return f'#flipper_{this_unit.direction}'
            elif this_unit.TYPE == 'piston':
                return f'#piston_{this_unit.direction}'
            elif this_unit.TYPE in UNITS:
                return f'#{this_unit.TYPE}'
            else:
                return '#OTHER'
        return '#EMPTY'

    def kill(self):
        self.group_id_textbox.kill()
        return super().kill()

    def update(self, time_delta):
        self.set_text(str(self.cell))
        self.group_id = None if self.cell.contents is None else self.cell.contents.IN_GROUP
        if self.group_id is not None:
            self.group_id_textbox.set_text(str(self.group_id))
            self.group_id_textbox.show()
        else:
            self.group_id_textbox.hide()
        return super().update(time_delta)


class FieldPanel(UIPanel):
    def __init__(self, manager, field, OPTIONS, **kwargs):
        self.OPTIONS = OPTIONS
        self.manager = manager
        self.field = field
        self.field_panel_rect = pygame.Rect(0, 0, 0, 0)
        # self.field_panel_rect.size = (160, 120)
        self.field_panel_rect.size = (
            ((BOARD_SIZE[1] + 3)*MARGIN + BOARD_SIZE[1]*CELL_SIZE[1]),  (BOARD_SIZE[0] + 3)*MARGIN + BOARD_SIZE[0]*CELL_SIZE[0])
        # self.field_panel_rect.topleft = (200, 0)
        self.field_panel_rect.topright = (WINDOW_SIZE[0]-MARGIN, MARGIN)
        super().__init__(self.field_panel_rect,
                         starting_layer_height=0, manager=manager, **kwargs)
        self.create_cells()

    def update_field(self, field):
        self.field = field
        for i in range(BOARD_SIZE[0]):
            for j in range(BOARD_SIZE[1]):
                if self.cells[i][j].object_id != self.cells[i][j].get_object_id():
                    self.cells[i][j] = UICell(
                        self.cells[i][j].relative_rect, field[i][j], self.manager, self.OPTIONS)

    def disable_uicells(self):
        for i in range(BOARD_SIZE[0]):
            for j in range(BOARD_SIZE[1]):
                self.cells[i][j].disable()

    def create_cells(self):
        start_x, start_y = (
            self.field_panel_rect.topleft[0] + 2*MARGIN, self.field_panel_rect.topleft[1] + 2*MARGIN)
        self.cells = [[UICell(relative_rect=pygame.Rect((start_x + j*(MARGIN + CELL_SIZE[0]), start_y + i*(MARGIN + CELL_SIZE[1])), CELL_SIZE),
                              cell=self.field[i][j],
                              manager=self.manager,
                              OPTIONS=self.OPTIONS) for j in range(BOARD_SIZE[1])] for i in range(BOARD_SIZE[0])]

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for i, cells_row in enumerate(self.cells):
                for j, cell in enumerate(cells_row):
                    if event.ui_element == cell:
                        print(self.field[i][j].contents.describe(
                        ) if self.field[i][j].contents is not None else f'pos={self.field[i][j].pos} empty cell')
        return super().process_event(event)

    def kill(self):
        for i in range(BOARD_SIZE[0]):
            for j in range(BOARD_SIZE[1]):
                self.cells[i][j].kill()

        return super().kill()


class CommandInput(UITextEntryLine):
    def __init__(self, manager, field_panel_rect, *args, **kwargs):
        rect = pygame.Rect((0, 0, 0, 0))
        rect.size = (field_panel_rect.size[0], COMMAND_INPUT_HEIGHT)
        rect.topright = field_panel_rect.bottomright
        super().__init__(rect, manager, *args, **kwargs)
        self.set_forbidden_characters(COMMAND_INPUT_FORBIDDEN_CHARS)


class CommandFeedback(UITextBox):
    def __init__(self, manager, field_panel_rect, command_input_rect, *args, **kwargs):
        rect = pygame.Rect((0, 0, 0, 0))
        rect.size = (field_panel_rect.size[0], WINDOW_SIZE[1] -
                     field_panel_rect.size[1] - COMMAND_INPUT_HEIGHT - MARGIN * 2)
        rect.topright = command_input_rect.bottomright
        super().__init__('', rect, manager, *args, **kwargs)


class LogTextBox(UITextBox):
    def __init__(self, manager, field_panel_rect: pygame.Rect, **kwargs):
        self.text = ''
        rect = pygame.Rect((0, 0, 0, 0))
        rect.size = (WINDOW_SIZE[0] - field_panel_rect.size[0] -
                     MARGIN * 2, field_panel_rect.size[1])
        rect.topright = field_panel_rect.topleft
        super().__init__(self.text, rect, manager, **kwargs)

    def log(self, text):
        self.append_html_text(text)


# class LettersSubmittedPanel(UIPanel):
#     pass


# class LettersStackPanel(UIPanel):
#     pass
class ManualMessage(UIMessageWindow):
    def __init__(self, manager):
        rect = pygame.Rect((200, 200), (700, 700))
        html_message = 'help'
        super().__init__(rect, html_message, manager, window_title='Manual')


class WinMessage(UIMessageWindow):
    def __init__(self, manager, words, submitted_word, command_history, *args, **kwargs):
        rect = pygame.Rect((200, 200), (600, 400))
        rect.center = (600, 400)
        to_show = [f'<font color=#4DE37C>{word}</font>' if word ==
                   submitted_word else word for word in words]
        html_message = 'You won!<br>' + \
            ' '.join(to_show) + '<br>' + 'Commands:<br>' + \
            ' '.join(command_history)
        super().__init__(rect, html_message, manager, *args, **kwargs)


class Gui(Game):
    def __init__(self, ui_manager, level_file):
        super().__init__(level_file)
        self.ui_manager = ui_manager
        self.field_panel = FieldPanel(
            self.ui_manager, self.field, self.OPTIONS)
        self.logs = LogTextBox(self.ui_manager, self.field_panel.rect)
        self.command_input = CommandInput(
            self.ui_manager, self.field_panel.rect)
        self.command_input.focus()
        self.command_feedback = CommandFeedback(
            self.ui_manager, self.field_panel.rect, self.command_input.rect)
        dummy_button_rect = pygame.Rect((0, 0, 0, 0))
        dummy_button_rect.size = (100, 60)
        dummy_button_rect.topright = self.logs.rect.bottomright
        self.dummy_button = UIButton(
            dummy_button_rect, 'DUMMY', self.ui_manager)
        self.dummy_button.hide()
        self.reset_multiline_cmds_mode()

        level_number,  = re.compile(
            r'.+level(.+).txt').search(level_file).groups()
        words_str = paint(' '.join(self.WORDS), '#E9D885')
        self.init_text = f'Level {paint(level_number, "#17D36A")} has been opened<br><br>' + \
            f'{paint("words")}: {paint("{")}{words_str}{paint("}")}<br>' + \
            (f'{paint("{")}{paint("<br>".join(self.NOTE), "#E19DD9")}{paint("}")}<br>' if self.NOTE else '')
        self.logs.log(self.init_text)

    def reset_multiline_cmds_mode(self):
        self.multiple_cmds_mode = SimpleNamespace(
            is_active=False, commands=[], commands_to_display=[],
            current_cmd_index=0, run=False, last_time=None, DELAY=None)

    def kill(self):
        self.field_panel.kill()
        self.logs.kill()
        self.command_input.kill()
        self.command_feedback.kill()
        self.dummy_button.kill()

    def reset_game_gui(self):
        pass
        # really prone to bugs
        # super().reset_game()
        # self.field_panel = FieldPanel(
        #     self.ui_manager, self.field, self.OPTIONS)

    def log_warning(self, w):
        self.logs.log(paint(f'{w.__class__.__name__} warning:<br>', '#F0BF0D'))
        self.logs.log(paint(f'[{w}]<br>'))

    def process_exception(self, e):
        self.log_exception(e)
        self.reset_multiline_cmds_mode()
        # self.reset_game()
        self.field_panel.disable_uicells()

    def log_exception(self, e):
        self.logs.log(
            paint(f'{e.__class__.__name__} exception:<br>', '#FF0000'))
        self.logs.log(paint(f'[{e}]<br>'))

    def try_execute_on_group(self, command):
        try:
            self.execute_on_group(command)
        except Warning as w:
            self.log_warning(w)
        except CustomException as e:
            self.process_exception(e)

    def process_event(self, event):
        if self.active:
            shift_mode = pygame.key.get_mods() & pygame.KMOD_SHIFT
            ctrl_mode = pygame.key.get_mods() & pygame.KMOD_CTRL
            if event.type == pygame.KEYDOWN:
                if shift_mode:
                    if not self.multiple_cmds_mode.is_active and event.key == pygame.K_RETURN:
                        # compile commands and activate multiple_cmds_mode
                        raw_commands = self.command_input.get_text()
                        self.command_input.set_text('')
                        try:
                            self.multiple_cmds_mode.commands, self.multiple_cmds_mode.commands_to_display = self.command_handler.get_command_sequence(
                                raw_commands)
                            self.command_history.append(raw_commands)
                            self.multiple_cmds_mode.is_active = True
                            self.command_input.unfocus()
                        except Warning as w:
                            self.log_warning(w)
                        except CustomException as e:
                            self.process_exception(e)
                elif ctrl_mode:
                    if self.multiple_cmds_mode.is_active and event.key == pygame.K_RETURN:
                        # run compiled commands
                        print('running')
                        self.multiple_cmds_mode.run = True
                        self.multiple_cmds_mode.delay = 4.0 / \
                            len(self.multiple_cmds_mode.commands)
                        self.multiple_cmds_mode.last_time = time()
                else:
                    if event.key == pygame.K_SLASH:
                        self.command_input.focus()
                    elif self.multiple_cmds_mode.is_active and event.key == pygame.K_RETURN:
                        # do one step in a sequence of compiled commands in multiple_cmd_mode
                        this_command = self.multiple_cmds_mode.commands[
                            self.multiple_cmds_mode.current_cmd_index]
                        self.try_execute_on_group(this_command)
                        self.multiple_cmds_mode.current_cmd_index += 1
                        if len(self.multiple_cmds_mode.commands) <= self.multiple_cmds_mode.current_cmd_index:
                            print('finish')
                            self.command_input.focus()
                            self.command_feedback.set_text('')
                            self.reset_multiline_cmds_mode()
                    elif self.multiple_cmds_mode.is_active and event.key == pygame.K_ESCAPE:
                        print('multiline_mode off')
                        self.command_feedback.set_text('')
                        self.reset_multiline_cmds_mode()
                    elif event.key == pygame.K_ESCAPE:
                        self.command_input.unfocus()
                    elif not self.multiple_cmds_mode.is_active and event.key == pygame.K_UP:
                        # insert previous prompt
                        if self.command_history:
                            self.command_input.set_text(
                                self.command_history[-1])
                    elif event.key == pygame.K_RETURN:
                        # run one single command
                        raw_command = self.command_input.get_text()
                        if raw_command.startswith('help'):
                            help = help_commands_processing(raw_command)
                            if help == '@manual':
                                ManualMessage(self.ui_manager)
                            else:
                                self.logs.log(help)
                            self.command_input.set_text('')
                        else:
                            try:
                                if not raw_command:
                                    raise EmptyPrompt(
                                        'There is nothing to execute')
                                if not self.command_handler.pattern_cmds.match(raw_command):
                                    raise NotASingleCommand(
                                        f'{raw_command} is not valid single-command; use [group_id][command] syntax')
                                single_command = self.command_handler.commands_on_single_group(
                                    raw_command)[0]
                                self.command_history.append(raw_command)
                                self.try_execute_on_group(single_command)
                            except Warning as w:
                                self.log_warning(w)
                    elif event.key == pygame.K_i:  # TODO: only when command_input is unfocused
                        # print out info about all objects and command history
                        for obj in self.objects:
                            print(obj.describe())
                        print('commands:', ' '.join(self.command_history))
                    elif event.key == pygame.K_DELETE:
                        pass
                        # print('reset_game')
                        # self.logs.log('reset game<br>')
                        # self.reset_game_gui()
            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.dummy_button:
                    print('hi')

            self.victory = self.is_victory()
            self.update()

    def update(self):
        if self.victory:
            WinMessage(self.ui_manager, self.WORDS, ''.join(
                self.submitted), command_history=self.command_history)
            self.command_feedback.set_text('')
            self.command_input.disable()
            self.command_feedback.disable()
            # self.field_panel.disable_uicells()
            print('commands:', ' '.join(self.command_history))
            self.active = False
        else:
            if self.multiple_cmds_mode.run and ((now := time()) - self.multiple_cmds_mode.last_time > self.multiple_cmds_mode.delay):
                if len(self.multiple_cmds_mode.commands) > self.multiple_cmds_mode.current_cmd_index:
                    self.multiple_cmds_mode.last_time = now
                    this_command = self.multiple_cmds_mode.commands[
                        self.multiple_cmds_mode.current_cmd_index]
                    self.try_execute_on_group(this_command)
                    self.multiple_cmds_mode.current_cmd_index += 1
                else:
                    print('finish')
                    self.command_input.focus()
                    self.command_feedback.set_text('')
                    self.reset_multiline_cmds_mode()
            self.field_panel.update_field(self.field)
            if self.multiple_cmds_mode.is_active:
                to_display = [paint(cmd, '#F0DE4A', size=4.5) if i == self.multiple_cmds_mode.current_cmd_index
                              else cmd for i, cmd in enumerate(self.multiple_cmds_mode.commands_to_display)]
                self.command_feedback.set_text(' '.join(to_display))


class LevelPicker():
    def __init__(self, manager, background, window_surface):
        self.level_filenames = load_level_filenames()
        self.manager = manager
        self.background = background
        self.window_surface = window_surface
        self.input_line_rect = pygame.Rect((0, 0, 0, 0))
        self.input_line_rect.topleft = (300, 100)
        self.input_line_rect.size = (600, 50)
        self.drop_down_level_picker = UIDropDownMenu(
            self.level_filenames, self.level_filenames[0], self.input_line_rect, self.manager)

        # import os
        # if os.path.exists('level_files/progress.json'):
        #     # keeps track of previously solved levels
        #     with open('progress.json', 'r') as f:
        #         self.progress = json.load(f)
        # else:
        #     self.progress = {
        #         filename: {'solved': False, 'solution': ''} for filename in self.level_filenames
        #     }

    def process_event(self, event):
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.drop_down_level_picker:
                self.opened_level = event.text
                solution = GameWindow(level_file='level_files/' + self.opened_level)
                pygame.display.set_caption('Pick a level...')
                # if solution:
                #     self.save_progress(solution)
    
    # def save_progress(self, solution):
    #     self.progress[self.opened_level]['solution'] = solution
    #     self.progress[self.opened_level]['solved'] = True
    #     with open('progress.json', 'w') as f:
    #             json.dump(self.progress, f)


def GameWindow(level_file):
    pygame.display.set_caption('Word Factory')
    window_surface = pygame.display.set_mode((WINDOW_SIZE[0], WINDOW_SIZE[1]))
    window_size = window_surface.get_rect().size
    background = pygame.Surface(window_size)
    background.fill(pygame.Color('#000000'))
    manager = pygame_gui.UIManager(
        window_size, theme_path='theme.json', enable_live_theme_updates=False)
    clock = pygame.time.Clock()
    exception_caught = False
    is_running = True

    try:
        game = Gui(manager, level_file)
    except LevelCreationError as e:
        # catching level creation exceptions
        exception_caught = True
        print(e)
        UIMessageWindow(pygame.Rect((200, 200), (700, 700)), paint(
            f'{e.__class__.__name__} exception:<br>{[e]}', '#FF0000'), manager)

    while is_running:
        time_delta = clock.tick(30)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

            if not exception_caught:
                game.process_event(event)

            manager.process_events(event)

        manager.update(time_delta)
        window_surface.blit(background, (0, 0))
        manager.draw_ui(window_surface)
        pygame.display.update()

    # if game.victory:
    #     return ' '.join(game.command_history)
    # else:
    #     return ''
    # game.kill()


def LevelPickerWindow():
    pygame.init()
    pygame.display.set_caption('Pick a level...')
    clock = pygame.time.Clock()
    window_surface = pygame.display.set_mode((WINDOW_SIZE[0], WINDOW_SIZE[1]))
    window_size = window_surface.get_rect().size
    background = pygame.Surface(window_size)
    background.fill(pygame.Color('#000000'))
    manager = pygame_gui.UIManager(
        window_size, theme_path='theme.json', enable_live_theme_updates=False)
    lvl_picker = LevelPicker(manager, background, window_surface)
    pygame_icon = pygame.image.load('assets/icon.png')
    pygame.display.set_icon(pygame_icon)

    is_running = True
    while is_running:
        time_delta = clock.tick(30)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            manager.process_events(event)
            lvl_picker.process_event(event)
        manager.update(time_delta)
        window_surface.blit(background, (0, 0))
        manager.draw_ui(window_surface)
        pygame.display.update()


def MenuWindow():
    pygame.init()
    pygame.display.set_caption('Word Factory')
    window_surface = pygame.display.set_mode((WINDOW_SIZE[0], WINDOW_SIZE[1]))
    pygame_icon = pygame.image.load('assets/icon.png')
    pygame.display.set_icon(pygame_icon)
    window_size = window_surface.get_rect().size
    background = pygame.Surface(window_size)
    background.fill(pygame.Color('#000000'))

    manager = pygame_gui.UIManager(
        window_size, theme_path='theme.json', enable_live_theme_updates=False)

    clock = pygame.time.Clock()

    is_running = True
    while is_running:
        time_delta = clock.tick(30)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    print('picker')
                    LevelPickerWindow()
            manager.process_events(event)

        manager.update(time_delta)
        window_surface.blit(background, (0, 0))
        manager.draw_ui(window_surface)
        pygame.display.update()


def main():
    LevelPickerWindow()


if __name__ == '__main__':
    main()
