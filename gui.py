# from copy import deepcopy
from copy import deepcopy
from types import SimpleNamespace
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIPanel, UITextEntryLine, UITextBox, UIWindow
from pygame_gui.windows import UIMessageWindow

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
        super().__init__(relative_rect, self.text, manager, **kwargs)
        rect_group_id = pygame.Rect(0, 0, 0, 0)
        rect_group_id.size = GROUP_ID_TEXTBOX_SIZE
        rect_group_id.topright = self.relative_rect.topright
        self.group_id_textbox = UITextBox('', rect_group_id, self.manager)
        self.group_id_textbox.hide()

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
                self.cells[i][j].cell = field[i][j]

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


class CommandInput(UITextEntryLine):
    def __init__(self, manager, field_panel_rect, *args, **kwargs):
        rect = pygame.Rect((0, 0, 0, 0))
        rect.size = (field_panel_rect.size[0], COMMAND_INPUT_HEIGHT)
        rect.topright = field_panel_rect.bottomright
        print('size', rect.size)
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


class LettersSubmittedPanel(UIPanel):
    pass


class LettersStackPanel(UIPanel):
    pass


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
        self.command_feedback = CommandFeedback(self.ui_manager, self.field_panel.rect, self.command_input.rect)

        words_str = paint(' '.join(self.WORDS), '#E9D885')
        self.logs.log(
            f'{paint("words")}: {paint("{")}{words_str}{paint("}")}<br>')
        if self.NOTE:
            self.logs.log(
                f'{paint("{")}{paint("<br>".join(self.NOTE), "#E19DD9")}{paint("}")}<br>')

    def reset_game_gui(self):
        # really prone to bugs
        super().reset_game()
        self.field_panel = FieldPanel(
            self.ui_manager, self.field, self.OPTIONS)

    def show_win_message(self):
        return WinMessage(self.ui_manager, self.WORDS, ''.join(self.submitted), command_history=self.command_history)

    def log_warning(self, w):
        self.logs.log(paint(f'{w.__class__.__name__} warning:<br>', '#F0BF0D'))
        self.logs.log(paint(f'[{w}]<br>'))

    def process_exception(self, e):
        self.log_exception(e)
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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SLASH:
                    self.command_input.focus()
                elif not self.multiple_cmds_mode.is_active and event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_SHIFT:
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
                elif self.multiple_cmds_mode.is_active and event.key == pygame.K_RETURN:
                    # do one step in a sequence in multiple_cmd_mode
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
                    self.command_input.set_text(self.command_history[-1])
                elif event.key == pygame.K_RETURN:
                    # run one single command
                    raw_command = self.command_input.get_text()
                    try:
                        single_command = self.command_handler.commands_on_single_group(
                            raw_command)[0]
                        self.command_history.append(raw_command)
                        self.try_execute_on_group(single_command)

                    except Warning as w:
                        self.log_warning(w)
                elif event.key == pygame.K_i:  # TODO: only when command_input is unfocused
                    # print info about all objects
                    for obj in self.objects:
                        print(obj.describe())
                    print('commands:', ' '.join(self.command_history))
                elif event.key == pygame.K_DELETE:
                    pass
                    # print('reset_game')
                    # self.logs.log('reset game<br>')
                    # self.reset_game_gui()
            self.victory = self.is_victory()
            self.update()

    def update(self):
        if self.victory:
            self.show_win_message()
            self.command_feedback.set_text('')
            self.command_input.disable()
            self.command_feedback.disable()
            # self.field_panel.disable_uicells()
            print('commands:', ' '.join(self.command_history))
            self.active = False
        else:
            self.field_panel.update_field(self.field)
            if self.multiple_cmds_mode.is_active:
                to_display = [paint(cmd, '#F1E970', size=4.25) if i == self.multiple_cmds_mode.current_cmd_index
                              else cmd for i, cmd in enumerate(self.multiple_cmds_mode.commands_to_display)]
                self.command_feedback.set_text(' '.join(to_display))


def main():
    pygame.init()
    pygame.display.set_caption('Word Factory')
    window_surface = pygame.display.set_mode((WINDOW_SIZE[0], WINDOW_SIZE[1]))
    window_size = window_surface.get_rect().size
    background = pygame.Surface(window_size)
    background.fill(pygame.Color('#000000'))

    manager = pygame_gui.UIManager(window_size)

    level_file = 'level_files/level_.txt'
    game = Gui(manager, level_file)
    clock = pygame.time.Clock()
    is_running = True

    while is_running:
        time_delta = clock.tick(30)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            game.process_event(event)
            manager.process_events(event)

        manager.update(time_delta)
        window_surface.blit(background, (0, 0))
        manager.draw_ui(window_surface)
        pygame.display.update()


if __name__ == '__main__':
    main()
