from copy import deepcopy
from types import SimpleNamespace
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIPanel, UITextEntryLine, UITextBox, UIWindow
from pygame_gui.windows import UIMessageWindow

from objects import Game
from exceptions import *
from utils import *


class UICell(UIButton):
    def __init__(self, relative_rect, text, manager, OPTIONS, unit_id=None, group_id=None, **kwargs):
        super().__init__(relative_rect, text, manager, **kwargs)
        self.unit_id = unit_id
        self.group_id = group_id
        if OPTIONS['show_ids'] and self.unit_id is not None:
            rect_unit_id = pygame.Rect(0, 0, 0, 0)
            rect_unit_id.size = 30, 30
            rect_unit_id.topleft = self.relative_rect.topleft
            self.unit_id_textbox = UITextBox(
                str(self.unit_id), rect_unit_id, manager)
        if self.group_id is not None:
            rect_group_id = pygame.Rect(0, 0, 0, 0)
            rect_group_id.size = 30, 30
            rect_group_id.topright = self.relative_rect.topright
            self.group_id_textbox = UITextBox(
                str(self.group_id), rect_group_id, manager)


class FieldPanel(UIPanel):
    def __init__(self, manager, field, OPTIONS, **kwargs):
        self.OPTIONS = OPTIONS
        self.manager = manager
        self.field = field
        field_panel_rect = pygame.Rect(
            (198, 1), (1002, 670))
        super().__init__(field_panel_rect, starting_layer_height=0, manager=manager, **kwargs)
        self.create_cells()

    def update_field(self, field):
        self.field = field
        for i in range(8):
            for j in range(12):
                self.cells[i][j].set_text(str(field[i][j]))

    def create_cells(self):
        margin = 3
        start_x = 200 + margin
        start_y = 0 + margin
        self.cells = [[UICell(relative_rect=pygame.Rect((start_x + j*(margin + CELL_SIZE[0]), start_y + i*(margin + CELL_SIZE[1])), CELL_SIZE),
                              text=str(self.field[i][j]),
                              manager=self.manager,
                              OPTIONS=self.OPTIONS,
                              unit_id=None if self.field[i][j].contents is None else self.field[i][j].contents.id,
                              group_id=None if self.field[i][j].contents is None else self.field[i][j].contents.IN_GROUP) for j in range(12)] for i in range(8)]

    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for i, cells_row in enumerate(self.cells):
                for j, cell in enumerate(cells_row):
                    if event.ui_element == cell:
                        print(i, j, self.field[i][j], type(
                            self.field[i][j].contents))
        return super().process_event(event)


class CommandInput(UITextEntryLine):
    def __init__(self, manager, *args, **kwargs):
        rect = pygame.Rect((198, 672), (1002, 40))
        super().__init__(rect, manager, *args, **kwargs)
        # self.set_allowed_characters(COMMAND_INPUT_ALLOWED_CHARS)
        self.set_forbidden_characters(COMMAND_INPUT_FORBIDDEN_CHARS)
        self.unfocus()


class CommandFeedback(UITextBox):
    def __init__(self, manager, *args, **kwargs):
        rect = pygame.Rect((198, 714), (1002, 70))
        super().__init__('', rect, manager, *args, **kwargs)


class LogTextBox(UITextBox):
    def __init__(self, manager, **kwargs):
        self.text = ''
        rect = pygame.Rect((1, 1), (198, 600))
        super().__init__(self.text, rect, manager, **kwargs)


class LettersSubmittedPanel(UIPanel):
    pass


class LettersStackPanel(UIPanel):
    pass


class WinMessage(UIMessageWindow):
    def __init__(self, manager, words, submitted_word, *args, **kwargs):
        rect = pygame.Rect((200, 200), (300, 200))
        rect.center = (600, 400)
        to_show = [f'<font color=#4DE37C>{word}</font>' if word ==
                   submitted_word else word for word in words]
        html_message = 'You won!<br>' + ' '.join(to_show)
        super().__init__(rect, html_message, manager, *args, **kwargs)


class Gui(Game):
    def __init__(self, ui_manager, level_file):
        super().__init__(level_file)
        self.ui_manager = ui_manager
        self.field_panel = FieldPanel(
            self.ui_manager, self.field, self.OPTIONS)
        self.command_input = CommandInput(self.ui_manager)
        self.command_feedback = CommandFeedback(self.ui_manager)
        self.logs = LogTextBox(self.ui_manager)

    def show_win_message(self):
        return WinMessage(self.ui_manager, self.WORDS, ''.join(self.submitted))

    def process_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.command_input.unfocus()
            elif event.key == pygame.K_SLASH:
                self.command_input.focus()
            elif not self.multiple_cmds_mode.is_active and event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                # compile commands
                self.multiple_cmds_mode.is_active = True
                self.command_input.unfocus()

                raw_commands = self.command_input.get_text()
                self.command_history.append(raw_commands)
                self.command_input.set_text('')
                self.command_handler.get_command_sequence(raw_commands)

                self.multiple_cmds_mode.commands = self.command_handler.result
                self.multiple_cmds_mode.commands_to_display = self.command_handler.result_to_display
            elif self.multiple_cmds_mode.is_active and event.key == pygame.K_RETURN:
                this_command = self.multiple_cmds_mode.commands[self.multiple_cmds_mode.current_cmd_index]
                print(this_command)
                try:
                    self.execute_on_group(this_command)
                except Warning as e:
                    print(e)
                    self.logs.append_html_text('warning<br>')

                self.multiple_cmds_mode.current_cmd_index += 1
                if len(self.multiple_cmds_mode.commands) <= self.multiple_cmds_mode.current_cmd_index:
                    print('finish')
                    self.command_feedback.set_text('')
                    self.multiple_cmds_mode = SimpleNamespace(
                        is_active=False, commands=[], commands_to_display=[], current_cmd_index=0)
                    self.command_handler.reset()
            elif not self.multiple_cmds_mode.is_active and event.key == pygame.K_UP:
                self.command_input.set_text(self.command_history[-1])
            elif event.key == pygame.K_RETURN:
                # run one command
                raw_command = self.command_input.get_text()
                single_command = self.command_handler.single_command(
                    raw_command)
                try:
                    self.execute_on_group(single_command)
                except Warning as e:
                    print(e)
                    self.logs.append_html_text('warning<br>')
                # self.command_feedback.append_html_text(command + ' ')
                # except Exception as e:
                #     print(e)
                #     self.logs.append_html_text('error')
                #     # self.field = deepcopy(self.field_initial_config)
                #     self.command_feedback.set_text('')
            # TODO: shift + Return = run programm
        if not self.victory:
            self.update()

    def update(self):
        self.field_panel.update_field(self.field)
        if self.multiple_cmds_mode.is_active:
            to_display = [f'<font color=#F1E970>{cmd}</font>' if i == self.multiple_cmds_mode.current_cmd_index
                          else cmd for i, cmd in enumerate(self.multiple_cmds_mode.commands_to_display)]
            self.command_feedback.set_text(' '.join(to_display))
        if self.is_victory():
            self.show_win_message()
            self.victory = True


def main():
    pygame.init()
    pygame.display.set_caption('Word Factory')
    window_surface = pygame.display.set_mode((1200, 800))
    window_size = window_surface.get_rect().size
    background = pygame.Surface(window_size)
    background.fill(pygame.Color('#000000'))
    manager = pygame_gui.UIManager(window_size)

    level_file = 'level_files/level2.txt'
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
        # game.update()
        window_surface.blit(background, (0, 0))
        manager.draw_ui(window_surface)
        pygame.display.update()


if __name__ == '__main__':
    main()
