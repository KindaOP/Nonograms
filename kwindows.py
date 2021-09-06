from __future__ import print_function

import pygame
import pygame.key
import pygame.font
import pygame.time
import pygame.event
import pygame.mixer
import pygame.mouse
import pygame.display
from pygame.transform import rotate

import os
import sys
import random
import platform
from typing import Union, Tuple

from kpuzzles import *
from kauxiliaries import KColor
from knonograms import KNonograms
from kobjects import KBlock, KTextBlock, KGrid, KGIF, KButton, KProgressBar

__version__ = '1.0.0'


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
        if KWindow._WINCOUNT == 0:
            print(f"Welcome to Nonograms - ver {__version__}")
            print(f"By KindaOP - Last updated: Sep 2021")
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
        opening_gif = KGIF(
            self.screen, 
            (100, 100),
            os.path.join(os.getcwd(), "Images", "interesting.gif"),
            Ts = 1
        )
        opening_gif.set_center(self.screen.get_rect().center)
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
            _p = (i+1)/n_frames
            opening_gif.surface.set_alpha(int(_p*255))
            opening_gif.draw()
            opening_gif.step()
            pbar.set_progress(_p)
            pbar.draw()
            pygame.display.flip()
            pygame.time.delay(50)
        pygame.time.delay(200)

    def start_menu(self):
        title = KGrid(
            KTextBlock(
                self.screen,
                "",
                50,
                (50, 50),
                (225, 100),
                color_default = KColor(255, 255, 255, 0),
                clickable = False
            ),
            (10, 1)
        )
        replace_title = lambda *ind_txt_clrn_tuples: title.replace(
            *tuple((
                (xi, yi),
                KTextBlock(
                    title.screen,
                    txt,
                    title.unit_origin.font_size,
                    title.unit_origin.rect.size,
                    title.unit_array[xi][yi].get_position(),
                    KColor.name(clrn),
                    title.unit_origin.color_default
                )) for (xi, yi), txt, clrn in ind_txt_clrn_tuples
            )
        )
        replace_title(
            ((0,0), "N", 'black'),
            ((1,0), "O", 'black'),
            ((2,0), "N", 'black'),
            ((3,0), "O", 'black'),
            ((4,0), "G", 'black'),
            ((5,0), "R", 'black'),
            ((6,0), "A", 'black'),
            ((7,0), "M", 'black'),
            ((8,0), "S", 'black'),
            ((9,0), "!", 'black')
        )
        tc = 0
        tnum = title.num_blocks[0]
        for xi in range(tnum):
            char = title.unit_array[xi][0]
            char.surface.set_alpha(0)
            char.inner_object.surface = rotate(
                char.inner_object.surface,
                random.randint(-30, 30) 
            )
        subtitle = KTextBlock(
            self.screen,
            f"- ver {__version__}",
            30,
            (100, 30),
            (700, 125),
            color_default = KColor(255, 255, 255, 0),
            clickable = False
        )
        subtitle.surface.set_alpha(0)
        subtitle.inner_object.surface = rotate(
            subtitle.inner_object.surface, 30
        )
        pygame.mixer.music.load(
            os.path.join(os.getcwd(), "Sounds", "opening.ogg")
        )
        pygame.mixer.music.play(loops=0)
        pygame.time.set_timer(KWindow.BG_CHANGE, millis=167,loops=6)
        while pygame.mixer.music.get_busy():
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == KWindow.BG_CHANGE:
                    self.screen.fill(KColor.random())
                    tc = tc + 2 
                    if tc <= tnum:
                        title.draw(
                            *tuple( (x,0) for x in range(tc) ),
                            bdin = False,
                            bdout = False
                        )
                    else:
                        title.draw(
                            *tuple( (x,0) for x in range(tnum) ),
                            bdin = False,
                            bdout = False
                        )
                        subtitle.draw()
            pygame.display.flip()
        buttons = (
            KButton(
                self.screen,
                "Start Game",
                50,
                (400, 50),
                (275, 350),
                KColor.name('blue').invert(),
                KColor.name('blue'),
                on_pressed = lambda: "start_game",
                on_released = None
            ),
            KButton(
                self.screen,
                "History",
                50,
                (400, 50),
                (275, 450),
                KColor.name('blue').invert(),
                KColor.name('blue'),
                on_pressed = lambda: "history",
                on_released = None
            ),
            KButton(
                self.screen,
                "Import Game",
                50,
                (400, 50),
                (275, 550),
                KColor.name('blue').invert(),
                KColor.name('blue'),
                on_pressed = lambda: "import_game",
                on_released = None
            ),
            KButton(
                self.screen,
                "Exit Game",
                50,
                (400, 50),
                (275, 650),
                KColor.name('blue').invert(),
                KColor.name('blue'),
                on_pressed = lambda: "exit_prompt",
                on_released = None
            )
        )
        for button in buttons:
            button.draw()
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        pygame.mixer.music.load(
            os.path.join(os.getcwd(), "Sounds", "looping.ogg")
        )
        pygame.mixer.music.play(loops=-1)
        target_page = str()
        while not target_page:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page = "exit_prompt"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    _mpos = pygame.mouse.get_pos()
                    for button in buttons:
                        clicked, target_page = button.check(_mpos)
                        if clicked:
                            break
                    if clicked:
                        continue
            pygame.display.flip()
        if target_page == "exit_prompt":
            KWindow._PREVPAGE = "start_menu"
        return target_page

    def start_game(self):
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
        nng.register(____PUZZLE01____)
        back_button = KButton(
                self.screen,
                "Back",
                50,
                (100, 50),
                (25, 25),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda: "start_menu",
                on_released = None
            )
        control_buttons = (
            KButton(
                self.screen,
                "Undo",
                40,
                (100, 50),
                (150, 25),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda nng: nng.undo(),
                on_released = None
            ),
            KButton(
                self.screen,
                "Redo",
                40,
                (100, 50),
                (275, 25),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda nng: nng.redo(),
                on_released = None
            ),
            KButton(
                self.screen,
                "Reset",
                40,
                (150, 50),
                (400, 25),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda nng: nng.reset(),
                on_released = None
            ),
            KButton(
                self.screen,
                "Restart",
                40,
                (150, 50),
                (575, 25),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda nng: nng.restart(),
                on_released = None
            ),
            KButton(
                self.screen,
                "CLR",
                25,
                (50, 50),
                (25, 100),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda nng: nng.scm(KBlock.EMPTY),
                on_released = None
            ),
            KButton(
                self.screen,
                "PNT",
                25,
                (50, 50),
                (25, 175),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda nng: nng.scm(KBlock.FILLED),
                on_released = None
            ),
            KButton(
                self.screen,
                "CRS",
                25,
                (50, 50),
                (25, 250),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda nng: nng.scm(KBlock.CROSSED),
                on_released = None
            ),
            KButton(
                self.screen,
                "DOT",
                25,
                (50, 50),
                (25, 325),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda nng: nng.scm(KBlock.DOTTED),
                on_released = None
            ),
            KButton(
                self.screen,
                "CHK",
                25,
                (50, 50),
                (25, 400),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda nng: nng.scm(KBlock.CHECKED),
                on_released = None
            )
        )
        back_button.draw()
        for cbutton in control_buttons:
            cbutton.draw()
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
                    checked, target_page = back_button.check(_mpos)
                    if checked:
                        break
                    for cbutton in control_buttons:
                        checked, _ = cbutton.check(_mpos, nng)
                        if checked:
                            break
                    if checked:
                        break
                    checked = nng.check(_mpos)
                    if checked:
                        break
                        
            pygame.display.flip()
        return target_page

    def history(self):
        self.screen.fill(self.color_bgdf)
        buttons = (
            KButton(
                self.screen,
                "Back",
                50,
                (100, 50),
                (25, 25),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda: "start_menu",
                on_released = None,
            ),
        )
        for button in buttons:
            button.draw()
        target_page = str()
        while not target_page:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page = "exit_prompt"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    _mpos = pygame.mouse.get_pos()
                    for button in buttons:
                        clicked, target_page = button.check(_mpos)
                        if clicked:
                            break
                    if clicked:
                        break
            pygame.display.flip()
        if target_page == "exit_prompt":
            KWindow._PREVPAGE = "history"
        return target_page

    def import_game(self):
        self.screen.fill(self.color_bgdf)
        buttons = (
            KButton(
                self.screen,
                "Back",
                50,
                (100, 50),
                (25, 25),
                KColor.name('white'),
                KColor.name('black'),
                on_pressed = lambda: "start_menu",
                on_released = None,
            ),
        )
        for button in buttons:
            button.draw()
        target_page = str()
        while not target_page:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page = "exit_prompt"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    _mpos = pygame.mouse.get_pos()
                    for button in buttons:
                        clicked, target_page = button.check(_mpos)
                        if clicked:
                            break
                    if clicked:
                        continue
            pygame.display.flip()
        if target_page == "exit_prompt":
            KWindow._PREVPAGE = "import_game"
        return target_page

    def exit_prompt(self):
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
        popup_buttons = (
            KButton(
                self.screen,
                "Yes",
                50,
                (150, 50),
                popup.get_position() + pygame.Vector2(30, 170),
                KColor.name('black'),
                KColor.name('white'),
                on_pressed = lambda: KWindow.EXIT,
                on_released = None,
            ),
            KButton(
                self.screen,
                "No",
                50,
                (150, 50),
                popup.get_position() + pygame.Vector2(270, 170),
                KColor.name('black'),
                KColor.name('white'),
                on_pressed = lambda: KWindow._PREVPAGE,
                on_released = None
            )
        )
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
            self.clock.tick(self.fps)
            self.current_page = eval(
                str().join(["self.", self.current_page, "()"])
            )
        self.closing_window()