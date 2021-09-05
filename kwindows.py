import pygame.key
import pygame.time
import pygame.event
import pygame.mixer
import pygame.mouse
import pygame.display

import sys
import platform

from knonograms import *


class KWindow():
    MUSIC_END = pygame.USEREVENT + 1
    BG_CHANGE = pygame.USEREVENT + 2

    EXIT = 'exit'
    _INITIALIZED = False
    _PREVPAGE = None
    _WINCOUNT = 0

    def __init__(
        self, 
        screen_size:Union[Tuple[int, int], None] = None, 
        color_bgdf:KColor = KColor.name('white'),
        current_page:str = "start_menu",
        fps:int = 30
        ):
        pygame.init()
        pygame.font.init()
        if screen_size is not None:
            self.screen_size = screen_size
        else:
            _system = platform.system()
            if _system == 'Linux':
                self.screen_size = (950, 950)
            elif _system == 'Windows':
                raise OSError("Windows sucks :P")
            else:
                raise OSError("program not supported by the OS")
        self.color_bgdf = color_bgdf
        self.current_page = current_page
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.screen = pygame.display.set_mode(self.screen_size)
        self.screen.fill(color_bgdf)
        _icon = pygame.Surface((32,32))
        icon_grid = KGrid(
            KBlock(
                _icon,
                (8, 8),
                (0, 0),
                KColor.name('black'),
                clickable = False
            ),
            (4, 4)
        )
        replace_color = lambda obj, *ind_clrname_tuple: obj.replace(
            *tuple((
                (xi, yi),
                KBlock(
                    obj.screen,
                    obj.unit_array[xi][yi].rect.size,
                    obj.unit_array[xi][yi].get_position(),
                    clrname
                )) for (xi, yi), clrname in ind_clrname_tuple
            ) 
        )
        replace_color(
            icon_grid,
            ( (0,0) , 'white' ),
            ( (1,1) , 'white' ),
            ( (2,3) , 'red' ),
            ( (3,3) , 'green' ),
            ( (3,2) , 'blue' )
        )
        icon_grid.draw_all()
        pygame.display.set_icon(_icon)
        KWindow._INITIALIZED = True
        KWindow._WINCOUNT += 1

    def __del__(self):
        KWindow._WINCOUNT -= 1
        if KWindow._WINCOUNT == 0:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            pygame.font.quit()
            pygame.quit()
            print("Thank You for Playing My Game! - KindaOP")

    def opening_window(self) -> None:
        print("opening_window")
        opening_gif = KGIF(
            self.screen, 
            (100, 100),
            os.path.join(os.getcwd(), "Images", "interesting.gif"),
            Ts = 1
        )
        pbar = KProgressBar(
            self.screen,
            (850, 50),
            (50, 850),
            progress = 0,
            color_pbg = self.color_bgdf
        )
        n_frames = len(opening_gif.frames)
        for i in range(n_frames):
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            pbar.set_progress((i+1)/n_frames)
            pbar.draw()
            opening_gif.draw()
            opening_gif.step()
            pygame.display.flip()
            pygame.time.delay(50)
        pygame.time.delay(500)

    def start_menu(self):
        print("start_menu")
        self.clock.tick(self.fps)
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        pygame.mixer.music.load(
            os.path.join(os.getcwd(), "Sounds", "opening.ogg")
        )
        pygame.mixer.music.play(loops=0)
        pygame.mixer.music.set_endevent(KWindow.MUSIC_END)
        self.screen.fill(KColor.random())
        pygame.time.set_timer(KWindow.BG_CHANGE, millis=200, loops=5)
        target_page = str()
        while not target_page:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page = "exit_prompt"
                    KWindow._PREVPAGE = "start_menu"
                elif event.type == KWindow.MUSIC_END:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                    pygame.mixer.music.load(
                        os.path.join(os.getcwd(), "Sounds", "looping.ogg")
                    )
                    pygame.mixer.music.play(loops=-1)
                    pygame.mixer.music.set_endevent()
                elif event.type == KWindow.BG_CHANGE:
                    self.screen.fill(KColor.random())
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    target_page = "start_game"
            pygame.display.flip()
        return target_page


    def start_game(self):
        print("start_game")
        self.screen.fill(self.color_bgdf)
        nng = KNonograms(
            self.screen,
            position = (100, 100),
            num_mainblocks = (25, 25),
            num_numblocks = (7, 7),
            size_mainblock = (25, 25),
            color_mainblocks = KColor.name('white'),
            color_numblocks = KColor.name('yellow')
        )
        button = KButton(
            self.screen,
            "Return",
            (100, 50),
            (25, 25),
            KColor.name('violet'),
            KColor.name('green'),
            on_pressed = lambda: "start_menu",
            on_released = None,
        )
        button.draw()
        nng.draw_all()
        target_page = str()
        while not target_page:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page = "exit_prompt"
                    KWindow._PREVPAGE = "start_menu"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    _mpos = pygame.mouse.get_pos()
                    checked, target_page = button.check(_mpos)
                    if checked:
                        continue
                    for key, grid in nng.grids.items():
                        ind = grid.block_index_at(_mpos)
                        if ind is not None:
                            print(ind)
                            break
                        
            pygame.display.flip()
        return target_page

    def history(self):
        print("history")
        target_page = str()
        while not target_page:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page == "exit_prompt"
                    KWindow._PREVPAGE = "history"
            pygame.display.flip()
        return target_page

    def import_game(self):
        print("import_game")
        target_page = str()
        while not target_page:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page == "exit_prompt"
                    KWindow._PREVPAGE = "import_game"
            pygame.display.flip()
        return target_page

    def exit_prompt(self):
        print("exit_prompt")
        popup = KTextBlock(
            self.screen,
            " Are you sure? ",
            90,
            (450, 250),
            (0, 0),
            is_centered = False
        )
        popup.set_center(self.screen.get_rect().center)
        popup.inner_object.rect.move_ip(0, 10)
        popup.surface.set_alpha(128)
        button_y = KButton(
            self.screen,
            "Yes",
            (150, 50),
            popup.get_position(),
            KColor.name('black'),
            KColor.name('white'),
            on_pressed = lambda: KWindow.EXIT,
            on_released = None,
        )
        button_y.set_position((
            popup.get_position() + pygame.Vector2(30, 170)
        ))
        button_n = KButton(
            self.screen,
            "No",
            (150, 50),
            popup.get_position(),
            KColor.name('black'),
            KColor.name('white'),
            on_pressed = lambda: KWindow._PREVPAGE,
            on_released = None
        )
        button_n.set_position((
            popup.get_position() + pygame.Vector2(270, 170)
        ))
        popup_buttons = button_y, button_n
        popup.draw()
        for button in popup_buttons:
            button.draw()
        target_page = str()
        while not target_page:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page = KWindow.EXIT
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    _mpos = pygame.mouse.get_pos()
                    for button in popup_buttons:
                        checked, target_page = button.check(_mpos)
                        if checked:
                            break
                    if checked:
                        continue
            pygame.display.flip()
        if target_page == KWindow._PREVPAGE:
            KWindow._PREVPAGE = None
        return target_page

    def closing_window(self) -> None:
        print("closing_window")
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        pygame.mixer.music.load(
            os.path.join(os.getcwd(), "Sounds", "closing.ogg")
        )
        pygame.mixer.music.play(loops=0)
        pygame.mixer.music.set_endevent(KWindow.MUSIC_END)
        self.screen.fill(self.color_bgdf)
        is_staying = True
        while is_staying:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_staying = False
                elif event.type == KWindow.MUSIC_END:
                    is_staying = False
            pygame.display.flip()

    def run(self) -> None:
        self.opening_window()
        while self.current_page != KWindow.EXIT:
            self.current_page = eval(
                str().join(["self.", self.current_page, "()"])
            )
        self.closing_window()