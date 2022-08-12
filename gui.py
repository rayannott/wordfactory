import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIPanel, UITextEntryLine

from objects import Game
from utils import *


class UICell(UIButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.disable()


class FieldPanel(UIPanel):
    def __init__(self, manager, *args, **kwargs):
        self.manager = manager
        self.field_win_rect = pygame.Rect(
            (198, 0), (1002, 670))
        starting_layer_height = 0
        super().__init__(self.field_win_rect, starting_layer_height, manager, *args, **kwargs)
        self.create_cells()

    def create_cells(self):
        margin = 3
        start_x = 200 + margin
        start_y = 0 + margin
        self.cells = [[UICell(relative_rect=pygame.Rect((start_x + j*(margin + CELL_SIZE[0]), start_y + i*(margin + CELL_SIZE[1])), CELL_SIZE),
                         text='',
                         manager=self.manager) for j in range(12)] for i in range(8)]
    
    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for i, cells_row in enumerate(self.cells):
                for j, cell in enumerate(cells_row):
                    if event.ui_element == cell:
                        print(i, j)
        return super().process_event(event)


class CommandInput(UITextEntryLine):
    def __init__(self, manager, *args, **kwargs):
        rect = pygame.Rect((198, 674), (1002, 40))
        super().__init__(rect, manager, *args, **kwargs)
        # self.set_allowed_characters(COMMAND_INPUT_ALLOWED_CHARS)
        self.set_forbidden_characters(COMMAND_INPUT_FORBIDDEN_CHARS)
        self.unfocus()


class Gui(Game):
    def __init__(self, ui_manager, WORDS):
        super().__init__(WORDS)
        self.ui_manager = ui_manager
        self.field_win = FieldPanel(self.ui_manager)
        self.command_input = CommandInput(self.ui_manager)

    def process_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.command_input.unfocus()
            elif event.key == pygame.K_SLASH:
                self.command_input.focus()


def main():

    pygame.init()

    pygame.display.set_caption('Word Factory')
    window_surface = pygame.display.set_mode((1200, 800))
    window_size = window_surface.get_rect().size
    print(window_size)
    background = pygame.Surface(window_size)
    background.fill(pygame.Color('#000000'))
    manager = pygame_gui.UIManager(window_size)

    words = ['hi', 'hike']
    game = Gui(manager, words)
    cursor_manager = None  # TODO
    clock = pygame.time.Clock()
    is_running = True

    while is_running:
        time_delta = clock.tick(60)/1000.0
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
