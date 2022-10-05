from time import time
from types import SimpleNamespace
from typing import List
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIPanel, UITextEntryLine, UITextBox, UIHorizontalSlider, UILabel
from pygame_gui.windows import UIMessageWindow
from pygame_gui.core import ObjectID

from objects import Cell, ConveyorBelt, Game, Manipulator, Rock
from exceptions import *
from sfx import bg_music_play, bg_music_set_vol, play_bg_music, play_sfx, set_sfx_volume
from utils import *

play_bg_music()

class UICell(UIButton):
    def __init__(self, relative_rect, cell: Cell, manager, **kwargs):
        self.cell = cell
        self.text = str(cell)
        self.manager = manager
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
            elif this_unit.TYPE == 'anvil':
                return f'#anvil'
            elif this_unit.TYPE == 'typo':
                return f'#typo{"_eliminated" if this_unit.eliminated else ""}'
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

# TODO: redraw


class FieldPanel(UIPanel):
    def __init__(self, manager, field, **kwargs):
        self.manager = manager
        self.field = field
        self.field_panel_rect = pygame.Rect(0, 0, 0, 0)
        self.field_panel_rect.size = (
            ((BOARD_SIZE[1] + 3)*MARGIN + BOARD_SIZE[1]*CELL_SIZE[1]),  (BOARD_SIZE[0] + 3)*MARGIN + BOARD_SIZE[0]*CELL_SIZE[0])
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
                        self.cells[i][j].relative_rect, field[i][j], self.manager)

    def disable_uicells(self):
        for i in range(BOARD_SIZE[0]):
            for j in range(BOARD_SIZE[1]):
                self.cells[i][j].disable()

    def create_cells(self):
        start_x, start_y = (
            self.field_panel_rect.topleft[0] + 2*MARGIN, self.field_panel_rect.topleft[1] + 2*MARGIN)
        self.cells = [[UICell(relative_rect=pygame.Rect((start_x + j*(MARGIN + CELL_SIZE[0]), start_y + i*(MARGIN + CELL_SIZE[1])), CELL_SIZE),
                              cell=self.field[i][j],
                              manager=self.manager) for j in range(BOARD_SIZE[1])] for i in range(BOARD_SIZE[0])]

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


class FieldPanelCreationWindow(FieldPanel):
    def __init__(self, manager, field, **kwargs):
        super().__init__(manager, field, **kwargs)

    def update_cursor(self, new_cursor):
        self.cursor = new_cursor

    def update_field(self):
        for i in range(BOARD_SIZE[0]):
            for j in range(BOARD_SIZE[1]):
                if self.cells[i][j].object_id != self.cells[i][j].get_object_id():
                    self.cells[i][j] = UICell(
                        self.cells[i][j].relative_rect, self.field[i][j], self.manager)

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for i, cells_row in enumerate(self.cells):
                for j, cell in enumerate(cells_row):
                    if event.ui_element == cell:
                        if self.cursor is None:
                            print('Nothing in the cursor')
                        else:
                            cell.cell.contents = self.cursor
                            self.field[i][j] = cell.cell
        return UIPanel.process_event(self, event)


class UnitsPanel(UIPanel):
    def __init__(self, manager, field_panel_rect, **kwargs):
        self.manager = manager
        rect = pygame.Rect((0, 0, 0, 0))
        rect.size = (WINDOW_SIZE[0] - field_panel_rect.size[0] -
                     MARGIN * 2, field_panel_rect.size[1])
        rect.topright = field_panel_rect.topleft
        super().__init__(rect,
                         starting_layer_height=0, manager=manager, **kwargs)


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

class SyntaxMessage(UIMessageWindow):
    def __init__(self, manager):
        rect = pygame.Rect((200, 200), (700, 700))
        html_message = '<br>'.join(SYNTAX_REF_TEXT) + '<br>'
        super().__init__(rect, html_message, manager, window_title='Syntax reference')

class ManualMessage(UIMessageWindow):
    def __init__(self, manager):
        rect = pygame.Rect((200, 200), (700, 700))
        html_message = '<br>'.join([
            f'---{paint(unit.capitalize(), "#0F7CFF")}---<br>{unit_help_text}<br>' for unit, unit_help_text in HELP_TEXT.items()
        ])
        super().__init__(rect, html_message, manager, window_title='Manual')


class WinMessage(UIMessageWindow):
    def __init__(self, manager, words, submitted_word, command_history, number_of_commands, *args, **kwargs):
        rect = pygame.Rect((200, 200), (600, 400))
        rect.center = (600, 400)
        to_show = [f'<font color=#4DE37C>{word}</font>' if word ==
                   submitted_word else word for word in words]
        html_message = 'You won!<br>' + \
            ' '.join(to_show) + '<br>' + 'Commands:<br>' + \
            ' '.join(command_history) + \
            f'<br>Number of commands: {number_of_commands}'
        super().__init__(rect, html_message, manager, *args, **kwargs)


class Gui(Game):
    def __init__(self, ui_manager, level_file):
        super().__init__(level_file)
        self.ui_manager = ui_manager
        self.field_panel = FieldPanel(
            self.ui_manager, self.field)
        self.logs = LogTextBox(self.ui_manager, self.field_panel.rect)
        self.command_input = CommandInput(
            self.ui_manager, self.field_panel.rect)
        self.command_input.focus()
        self.command_feedback = CommandFeedback(
            self.ui_manager, self.field_panel.rect, self.command_input.rect)
        self.notifications_shown = SimpleNamespace(
            typos_left=False, typos_eliminated=False)


        exit_button_rect = pygame.Rect((0, 0), (100, COMMAND_INPUT_HEIGHT))
        exit_button_rect.topright = self.logs.rect.bottomright
        self.exit_button = UIButton(
            exit_button_rect, 'Exit', self.ui_manager, starting_height=2, tool_tip_text='all current progress will be lost')

        reset_button_rect = pygame.Rect((0, 0), (100, COMMAND_INPUT_HEIGHT))
        reset_button_rect.topleft = exit_button_rect.bottomleft
        self.reset_button = UIButton(
            reset_button_rect, 'Reset', self.ui_manager, starting_height=2, tool_tip_text='all current progress will be lost too')
        
        self.reset_multiline_cmds_mode()

        level_number = get_level_number_from_filename(level_file)
        words_str = paint(' '.join(self.WORDS), '#E9D885', size=5)
        self.init_text = f'Level {paint(level_number, "#17D36A")}. {paint(self.NAME, "#4455FF")}<br>' + \
            f'{paint("goal")}: {paint("{")}{words_str}{paint("}")}<br>' + \
            (f'{paint("{")}{paint("<br>".join(self.NOTE), "#E19DD9")}{paint("}")}<br>' if self.NOTE else '')
        self.logs.log(self.init_text)

    def reset_multiline_cmds_mode(self):
        self.multiple_cmds_mode = SimpleNamespace(
            is_active=False, commands=[], commands_to_display=[],
            current_cmd_index=0, run=False, last_time=None, DELAY=None)

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
            play_sfx('warning')
        except CustomException as e:
            self.process_exception(e)
            play_sfx('exception')

    def process_event(self, event):
        if self.active:
            shift_mode = pygame.key.get_mods() & pygame.KMOD_SHIFT
            if event.type == pygame.KEYDOWN:
                if shift_mode:
                    if not self.multiple_cmds_mode.is_active and event.key == pygame.K_RETURN:
                        # compile commands and activate multiple_cmds_mode
                        raw_command = self.command_input.get_text()
                        self.command_history.append(raw_command)
                        self.command_input.set_text('')
                        try:
                            self.multiple_cmds_mode.commands, self.multiple_cmds_mode.commands_to_display = self.command_handler.get_command_sequence(
                                raw_command)
                            self.multiple_cmds_mode.is_active = True
                            self.command_input.unfocus()
                            print('start steps')
                        except Warning as w:
                            self.log_warning(w)
                        except CustomException as e:
                            self.process_exception(e)
                else:
                    if event.key == pygame.K_RETURN:
                        raw_command = self.command_input.get_text()
                        if raw_command.startswith('-'):
                            # run console commands
                            if raw_command.startswith('-help'):
                                self.logs.log(
                                    f'{paint("CONSOLE", "#FA1041")}: requested help<br>')
                                help = help_commands_processing(raw_command)
                                if help == '@manual':
                                    ManualMessage(self.ui_manager)
                                elif help == '@syntax':
                                    SyntaxMessage(self.ui_manager)
                                else:
                                    self.logs.log(help)
                            elif raw_command == '-info':
                                # print out info about all objects and command history
                                print('--- GAME INFO ---')
                                for obj in self.objects:
                                    print(obj.describe())
                                print('typos:', ' '.join(
                                    [f'{typo.pos}{typo.eliminated}' for typo in self.typos]))
                                print('commands:', ' '.join(
                                    self.command_history))
                                print('number of commands:', self.number_of_commands)
                                self.logs.log(
                                    f'{paint("CONSOLE", "#FA1041")}: game information has been printed to the console<br>')
                            elif raw_command == '-clear':
                                print('clearing')
                                self.logs = LogTextBox(self.ui_manager, self.field_panel.rect)
                                self.logs.log(self.init_text)
                            else:
                                self.logs.log(
                                    f'{paint("CONSOLE", "#FA1041")}: try typing "-help"<br>')
                        else:
                            if not self.multiple_cmds_mode.is_active:
                                raw_command = self.command_input.get_text()
                                print('instant execution: ', raw_command)
                                self.command_history.append(raw_command)
                                try:
                                    commands_, _ = self.command_handler.get_command_sequence(
                                        raw_command)
                                    for cmd_ in commands_:
                                        self.try_execute_on_group(cmd_)
                                except Warning as w:
                                    play_sfx('prompt_warning')
                                    self.log_warning(w)
                                except CustomException as e:
                                    self.process_exception(e)
                            else:
                                # do one step in a sequence of compiled commands in multiple_cmd_mode
                                this_command = self.multiple_cmds_mode.commands[
                                    self.multiple_cmds_mode.current_cmd_index]
                                self.try_execute_on_group(this_command)
                                self.multiple_cmds_mode.current_cmd_index += 1
                                if len(self.multiple_cmds_mode.commands) <= self.multiple_cmds_mode.current_cmd_index:
                                    print('end steps')
                                    self.command_input.focus()
                                    self.command_feedback.set_text('')
                                    self.reset_multiline_cmds_mode()
                        self.command_input.set_text('')
                    elif event.key == pygame.K_SLASH:
                        self.command_input.focus()
                    elif event.key == pygame.K_ESCAPE:
                        if self.multiple_cmds_mode.is_active:
                            print('multiline_mode off')
                            self.command_feedback.set_text('')
                            self.reset_multiline_cmds_mode()
                        else:
                            self.command_input.unfocus()
                    elif not self.multiple_cmds_mode.is_active and event.key == pygame.K_UP:
                        # insert previous prompt
                        if self.command_history:
                            self.command_input.set_text(
                                self.command_history[-1])
                                
            word_created, typos_eliminated = self.is_victory()
            self.victory = word_created and typos_eliminated
            if not self.notifications_shown.typos_left and word_created and not typos_eliminated:
                self.logs.log(
                    paint('There are some typos left!<br>', '#F0BF0D'))
                self.notifications_shown.typos_left = True
            if not self.notifications_shown.typos_eliminated and typos_eliminated and self.typos:
                self.logs.log(paint('No typos (left)!<br>', '#88F07D'))
                self.notifications_shown.typos_eliminated = True
                play_sfx('typos_eliminated')
            self.update()

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            play_sfx('cool_click_up')
            if event.ui_element == self.exit_button:
                self.is_running = False
            elif event.ui_element == self.reset_button:
                UIMessageWindow(pygame.Rect(400, 300, 400, 400), 'Sorry, this does nothing', self.ui_manager)
                play_sfx('fart')
        elif event.type == pygame_gui.UI_BUTTON_START_PRESS:
            play_sfx('cool_click_down')

        

    def update(self):
        if self.victory:
            play_sfx('victory')
            WinMessage(self.ui_manager, self.WORDS, ''.join(
                self.submitted), command_history=self.command_history, number_of_commands=self.number_of_commands)
            self.command_feedback.set_text('')
            self.command_input.disable()
            self.command_feedback.disable()
            self.field_panel.update_field(self.field)
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

class PickLevelButton(UIButton):
    def __init__(self, relative_rect, manager, button_text, filename, text_box_text, *args, **kwargs):
        button_rect = pygame.Rect(relative_rect.topleft, (relative_rect.width, relative_rect.height*0.6))
        text_box_rect = pygame.Rect(button_rect.bottomleft, (relative_rect.width, relative_rect.height*0.4))
        self.level_filename = filename
        super().__init__(button_rect, button_text, manager, tool_tip_text=filename)
        self.textbox = UITextBox(text_box_text, text_box_rect, manager)

class LevelButtonsPanel(UIPanel):
    def __init__(self, manager, level_filenames, **kwargs):
        self.level_filenames = level_filenames
        # self.progress = progress
        self.panel_rect = pygame.Rect((0, 0, 0, 0))
        self.panel_rect.topleft = (MARGIN, MARGIN)
        self.button_size = (121, 80)
        self.panel_rect.size = (LEVELS_GRID_SIZE[0]*(self.button_size[0] + MARGIN) + 3*MARGIN, WINDOW_SIZE[1]-2*MARGIN)
        self.manager = manager
        super().__init__(self.panel_rect, starting_layer_height=0,
                         manager=self.manager, **kwargs)
        self.progress_data_dict = load_progress_data()
        self.create_buttons()

    def create_buttons(self):
        amount = len(self.level_filenames)
        start_x, start_y = (
            self.panel_rect.topleft[0] + 2*MARGIN, self.panel_rect.topleft[1] + 2*MARGIN)
        self.buttons: List[PickLevelButton] = []
        for k in range(amount):
            j = k % LEVELS_GRID_SIZE[0]
            i = k // LEVELS_GRID_SIZE[0]
            button_text = f'Level {get_level_number_from_filename(self.level_filenames[k])}'
            self.buttons.append(PickLevelButton(relative_rect=pygame.Rect((start_x + j*(MARGIN + self.button_size[0]), start_y + i*(MARGIN + self.button_size[1])),
                                self.button_size), manager=self.manager, button_text=button_text, filename=self.level_filenames[k], text_box_text=''))
            self.update_textbox_fields()

    def update_textbox_fields(self):
        for btn in self.buttons:
            level_data_dict = self.progress_data_dict.get(btn.level_filename)
            if level_data_dict:
                tb_list = []
                tooltip_list = []
                for word, word_data in level_data_dict.items():
                    tb_list.append(paint(word_data["num_of_cmds"], color="#0FFF0F"))
                    tooltip_list.append(word)
                btn.tool_tip_text = '|'.join(tooltip_list)
                tb_text = 'sol: ' + '|'.join(tb_list)
            else:
                tb_text = paint('no solution', color='#707070')
            btn.textbox.set_text(tb_text)

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for i, btn in enumerate(self.buttons):
                if event.ui_element == btn:
                    self.opened_level = self.level_filenames[i]
                    solution = GameWindow(
                        level_file=LEVELS_DIR + '/' + self.opened_level)
                    if solution:
                        print('sol:', solution)
                        update_solution(self.progress_data_dict, self.opened_level, *solution)
                        self.update_textbox_fields()
                    pygame.display.set_caption('Pick a level...')
        return super().process_event(event)

class SettingsPanel(UIPanel):
    def __init__(self, manager, levels_panel_rect):
        self.panel_rect = pygame.Rect((0, 0, 0, 0))
        self.panel_rect.topleft = levels_panel_rect.topright
        self.panel_rect.size = (WINDOW_SIZE[0] - levels_panel_rect.width - 2*MARGIN, WINDOW_SIZE[1] - 2*MARGIN)
        self.manager = manager
        super().__init__(self.panel_rect, 0, self.manager)
        APPROPRIATE_WIDTH = self.panel_rect.width - 2*MARGIN
        music_vol_label_rect = pygame.Rect(shift(self.panel_rect.topleft, (MARGIN, MARGIN)), (APPROPRIATE_WIDTH, 30))
        self.music_volume_tb = UITextBox(f'music volume: {self.volume_string(MUSIC_DEFAULT_VOLUME)}', music_vol_label_rect, self.manager)
        music_slider_rect = pygame.Rect(music_vol_label_rect.bottomleft, (APPROPRIATE_WIDTH, 50))
        self.music_volume_slider = UIHorizontalSlider(music_slider_rect, MUSIC_DEFAULT_VOLUME, (0.0, 1.0), self.manager)

        sfx_vol_label_rect = pygame.Rect(shift(music_slider_rect.bottomleft, (MARGIN, 2*MARGIN)), (APPROPRIATE_WIDTH, 30))
        self.sfx_volume_tb = UITextBox(f'sfx volume: {self.volume_string(SFX_DEFAULT_VOLUME)}', sfx_vol_label_rect, self.manager)
        sfx_slider_rect = pygame.Rect(sfx_vol_label_rect.bottomleft, (APPROPRIATE_WIDTH, 50))
        self.sfx_volume_slider = UIHorizontalSlider(sfx_slider_rect, SFX_DEFAULT_VOLUME, (0.0, 1.0), self.manager)
    
    @staticmethod
    def volume_string(value) -> str:
        return paint_linear(f'{value:.0%}', value, (0, 1), ((255,255,255),(0,255,0)))

    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.music_volume_slider:
                current_slider_value = self.music_volume_slider.get_current_value()
                if current_slider_value == 0:
                    bg_music_play(False)
                else:
                    bg_music_play(True)
                    bg_music_set_vol(current_slider_value)
                self.music_volume_tb.set_text(f'music volume: {self.volume_string(current_slider_value)}')
            elif event.ui_element == self.sfx_volume_slider:
                current_slider_value = self.sfx_volume_slider.get_current_value()
                set_sfx_volume(current_slider_value)
                self.sfx_volume_tb.set_text(f'sfx volume: {self.volume_string(current_slider_value)}')
        elif event.type == pygame_gui.UI_BUTTON_START_PRESS:
            play_sfx('cool_click_down')
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            play_sfx('cool_click_up')

        return super().process_event(event)

class LevelPicker():
    def __init__(self, manager, background, window_surface):
        self.level_filenames = load_level_filenames()
        self.manager = manager
        self.background = background
        self.window_surface = window_surface
        self.level_buttons_panel = LevelButtonsPanel(
            self.manager, self.level_filenames)
        self.settings_panel = SettingsPanel(self.manager, self.level_buttons_panel.panel_rect)
        self.chosen_button_index = 0
        self.chosen_button_index_prev = 0

    def process_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                from random import choice
                this_level = choice(self.level_filenames)
                solution = GameWindow(
                    level_file=LEVELS_DIR + '/' + this_level)
                if solution:
                    print('sol:', solution)
                pygame.display.set_caption('Pick a level...')
            elif event.key == pygame.K_RETURN:
                print(
                    'selected:', self.level_buttons_panel.buttons[self.chosen_button_index].text)
                this_level = self.level_buttons_panel.level_filenames[self.chosen_button_index]
                solution = GameWindow(
                    level_file=LEVELS_DIR + '/' + this_level)
                if solution:
                    print('sol:', solution)
                pygame.display.set_caption('Pick a level...')
            elif event.key == pygame.K_UP and self.chosen_button_index - LEVELS_GRID_SIZE[0] >= 0:
                self.chosen_button_index_prev = self.chosen_button_index
                self.level_buttons_panel.buttons[self.chosen_button_index].unselect(
                )
                self.chosen_button_index -= LEVELS_GRID_SIZE[0]
                # self.chosen_button_index %= LEVELS_GRID_SIZE[1]
                self.level_buttons_panel.buttons[self.chosen_button_index].select(
                )
            elif event.key == pygame.K_RIGHT and self.chosen_button_index < len(self.level_buttons_panel.buttons) - 1:
                self.chosen_button_index_prev = self.chosen_button_index
                self.level_buttons_panel.buttons[self.chosen_button_index].unselect(
                )
                self.chosen_button_index += 1
                # self.chosen_button_index %= LEVELS_GRID_SIZE[0]
                self.level_buttons_panel.buttons[self.chosen_button_index].select(
                )
            elif event.key == pygame.K_DOWN and self.chosen_button_index + LEVELS_GRID_SIZE[0] < len(self.level_buttons_panel.buttons):
                self.chosen_button_index_prev = self.chosen_button_index
                self.level_buttons_panel.buttons[self.chosen_button_index].unselect(
                )
                self.chosen_button_index += LEVELS_GRID_SIZE[0]
                # self.chosen_button_index %= LEVELS_GRID_SIZE[1]
                self.level_buttons_panel.buttons[self.chosen_button_index].select(
                )
            elif event.key == pygame.K_LEFT and self.chosen_button_index > 0:
                self.chosen_button_index_prev = self.chosen_button_index
                self.level_buttons_panel.buttons[self.chosen_button_index].unselect(
                )
                self.chosen_button_index -= 1
                # self.chosen_button_index %= LEVELS_GRID_SIZE[0]
                self.level_buttons_panel.buttons[self.chosen_button_index].select(
                )


def GameWindow(level_file):
    pygame.display.set_caption('Word Factory')
    window_surface = pygame.display.set_mode((WINDOW_SIZE[0], WINDOW_SIZE[1]))
    window_size = window_surface.get_rect().size
    background = pygame.Surface(window_size)
    background.fill(pygame.Color('#000000'))
    manager = pygame_gui.UIManager(
        window_size, theme_path='theme.json', enable_live_theme_updates=False)
    pygame_icon = pygame.image.load('assets/icon.png')
    pygame.display.set_icon(pygame_icon)
    clock = pygame.time.Clock()
    exception_caught = False

    try:
        game = Gui(manager, level_file)
    except LevelCreationError as e:
        # catching level creation exceptions
        exception_caught = True
        print(e)
        UIMessageWindow(pygame.Rect((200, 200), (700, 700)), paint(
            f'{e.__class__.__name__} exception:<br>[{e}]', '#FF0F0F'), manager)

    while game.is_running:
        time_delta = clock.tick(FRAMERATE)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.is_running = False
            if not exception_caught:
                game.process_event(event)
            manager.process_events(event)
        manager.update(time_delta)
        window_surface.blit(background, (0, 0))
        manager.draw_ui(window_surface)
        pygame.display.update()

    if not exception_caught and game.victory:
        return (''.join(game.submitted), game.number_of_commands, ' '.join(game.command_history))
    


def LevelCreationWindow():
    pygame.init()
    pygame.display.set_caption('Pick a level...')
    clock = pygame.time.Clock()
    window_surface = pygame.display.set_mode((WINDOW_SIZE[0], WINDOW_SIZE[1]))
    window_size = window_surface.get_rect().size
    background = pygame.Surface(window_size)
    background.fill(pygame.Color('#000000'))
    manager = pygame_gui.UIManager(
        window_size, theme_path='theme.json', enable_live_theme_updates=False)
    level_creator = LevelCreator(manager, background, window_size)

    is_running = True
    while is_running:
        time_delta = clock.tick(FRAMERATE)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            manager.process_events(event)
            level_creator.process_event(event)
        manager.update(time_delta)
        window_surface.blit(background, (0, 0))
        manager.draw_ui(window_surface)
        pygame.display.update()


class LevelCreator:
    def __init__(self, manager, background, window_surface):
        self.manager = manager
        self.background = background
        self.window_surface = window_surface
        self.cursor = None
        self.id = 0
        self.field: List[List[Cell]] = [[Cell(pos=(i, j)) for j in range(BOARD_SIZE[1])]
                                        for i in range(BOARD_SIZE[0])]
        self.field_panel = FieldPanelCreationWindow(self.manager, self.field)

        self.units_panel = UnitsPanel(
            self.manager, self.field_panel.field_panel_rect)

    def process_event(self, event):
        self.update()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                for i, _row in enumerate(self.field):
                    for j, _el in enumerate(_row):
                        print(_el.contents, sep=' ')
                    print('___')
            elif event.key == pygame.K_m:
                self.cursor = Manipulator(self.id, None)
            elif event.key == pygame.K_c:
                self.cursor = ConveyorBelt(self.id, None)
            elif event.key == pygame.K_r:
                self.cursor = Rock(self.id, None)

    def update(self):
        self.field_panel.update_cursor(self.cursor)
        self.field = self.field_panel.field
        self.field_panel.update_field()


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
        time_delta = clock.tick(FRAMERATE)/1000.0
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
        time_delta = clock.tick(FRAMERATE)/1000.0
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
    # LevelCreationWindow()


if __name__ == '__main__':
    main()
