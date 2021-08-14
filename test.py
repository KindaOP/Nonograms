
import pygame
import pygame.key
import pygame.draw
import pygame.font
import pygame.time
import pygame.event
import pygame.image
import pygame.mixer
import pygame.mouse
import pygame.display
from pygame.colordict import THECOLORS

import os
import sys
import random
from time import time
from PIL import Image
from typing import Any, Callable, Dict, List, Union, Tuple


class KindaType():

    Position2D = Union[Tuple[int, int], pygame.Vector2]


class KindaEvent():

    MUSIC_END = pygame.USEREVENT + 1
    BG_CHANGE = pygame.USEREVENT + 2


class KindaColor(pygame.Color):

    def __init__(self, r: int, g: int, b: int, a: int = 255):
        super(KindaColor, self).__init__(r, g, b, a)

    @classmethod
    def from_colordict(cls, name: str):
        return cls(*THECOLORS[name])

    @classmethod
    def random(cls, alpha: bool = False):
        return cls(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255) if alpha else 255
        )

    @classmethod
    def random_binary(cls):
        _val = random.randint(0, 255)
        return cls(_val, _val, _val, 255)


class _KindaObject():

    def __init__(
        self,
        surface: pygame.Surface,
        position: KindaType.Position2D
    ):
        self.surface = surface
        self.rect = pygame.Rect(*position, *surface.get_size())

    @classmethod
    def _from_pyrect(cls, rect: pygame.Rect):
        return cls(pygame.Surface(rect.size), rect.topleft)

    def _copy_to(self, position: KindaType.Position2D):
        return _KindaObject(self.surface, position)

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.surface, self.rect)

    def shift(self, dx: int, dy: int) -> None:
        self.rect.move_ip(dx, dy)

    def get_pos(self) -> pygame.Vector2:
        return self.rect.topleft

    def set_pos(self, position: KindaType.Position2D) -> None:
        _shift = pygame.Vector2(position) - self.get_pos()
        self.shift(*_shift)

    def get_center(self) -> pygame.Vector2:
        return self.rect.center

    def set_center(self, position: KindaType.Position2D) -> None:
        _shift = pygame.Vector2(position) - self.get_center()
        self.shift(*_shift)

    def is_enclosing(
        self,
        position: KindaType.Position2D,
        boundary=True
    ) -> bool:
        _x, _y = position
        _xi, _xf = self.rect.left, self.rect.right
        _yi, _yf = self.rect.top, self.rect.bottom
        _hbnd = _x >= _xi and _x <= _xf if boundary else _x > _xi and _x < _xf
        _vbnd = _y >= _yi and _y <= _yf if boundary else _y > _yi and _y < _yf
        return _hbnd and _vbnd
        

class KindaGIF(_KindaObject):

    def __init__(
            self,
            fpath: str,
            period: int,
            position: KindaType.Position2D):
        _frames = list()

        def add_pyimage(img: Image) -> None:
            nonlocal _frames
            _img = img.convert('RGBA')
            _frames.append(
                pygame.image.fromstring(
                    _img.tobytes(),
                    _img.size,
                    _img.mode
                ).convert_alpha()
            )
        with Image.open(fpath) as image:
            add_pyimage(image)
            while True:
                try:
                    image.seek(image.tell()+period)
                except EOFError:
                    break
                else:
                    add_pyimage(image)
        self.frames = _frames
        self.num_frames = len(_frames)
        self.findex = 0
        super(KindaGIF, self).__init__(
            self.frames[self.findex],
            position
        )

    def step(self, reversed=False) -> None:
        if reversed:
            _next = self.findex-1
            self.findex = self.num_frames-1 if _next == -1 else _next
        else:
            _next = self.findex+1
            self.findex = 0 if _next == self.num_frames else _next
        self.surface = self.frames[self.findex]



class KindaBlock(_KindaObject):

    EMPTY = 0
    FILLED = 1
    DOTTED = 2
    CROSSED = 3

    def __init__(
        self,
        size: Tuple[int, int],
        position: KindaType.Position2D,
        dfcolor: KindaColor,
        detect: bool = False,
        inner_factor: float = 0.6
    ) -> None:
        super(KindaBlock, self).__init__(pygame.Surface(size), position)
        self.dfcolor = dfcolor
        self.surface.fill(dfcolor)
        self.color = dfcolor
        self.state = KindaBlock.EMPTY
        self.detect = detect
        self.inobj = _KindaObject._from_pyrect(
            pygame.Rect(
                *self.get_pos(),
                *(inner_factor * pygame.Vector2(self.surface.get_size()))
            )
        )
        self.inobj.set_center(self.get_center())
        self.indot = _KindaObject._from_pyrect(
            pygame.Rect(
                *self.get_pos(),
                *((1-inner_factor) * pygame.Vector2(self.surface.get_size()))
            )
        )
        self.indot.set_center(self.get_center())
        self.indot.surface.fill(KindaColor.from_colordict('black'))
        self.infactor = inner_factor
        self.incontent = None

    def _set_color(self, color: KindaColor) -> None:
        self.surface.fill(color)
        self.color = color

    def draw(self, screen:pygame.Surface) -> None:
        super(KindaBlock, self).draw(screen)
        if self.incontent != None:
            self.incontent.draw(screen)
        if self.state == KindaBlock.CROSSED:
            _inrect = self.inobj.rect
            pygame.draw.line(
                screen,
                KindaColor.from_colordict('black'),
                _inrect.topleft,
                _inrect.bottomright,
                width=3
            )
            pygame.draw.line(
                screen,
                KindaColor.from_colordict('black'),
                _inrect.bottomleft,
                _inrect.topright,
                width=3
            )
        elif self.state == KindaBlock.DOTTED:
            self.indot.draw(screen)

    def set_state(self, state: int, fill_color: Union[KindaColor, None] = None) -> None:
        if state == KindaBlock.EMPTY:
            self._set_color(self.dfcolor)
        elif state == KindaBlock.FILLED:
            self._set_color(fill_color)
        elif state == KindaBlock.CROSSED or state == KindaBlock.DOTTED:
            self._set_color(self.dfcolor)
        self.state = state

    def copy_to(self, position: KindaType.Position2D):
        _obj = KindaBlock(
            self.surface.get_size(),
            position,
            self.dfcolor,
            self.detect,
            self.infactor,
        )
        _obj._set_color(self.color)
        _obj.set_state(self.state)
        return _obj


class KindaTextBlock(KindaBlock):

    def __init__(
        self,
        text: str,
        fsize: int,
        size: Tuple[int, int],
        position: KindaType.Position2D,
        dfcolor: KindaColor,
        detect: bool = True,
        inner_factor: float = 0.6,
    ) -> None:
        super(KindaTextBlock, self).__init__(
            size, position, dfcolor, detect, inner_factor
        )
        self.text = text
        self.fsize = fsize
        self.incontent = _KindaObject(
            pygame.font.Font.render(
                pygame.font.SysFont(
                    pygame.font.get_default_font(),
                    fsize
                ),
                text,
                True,
                KindaColor.from_colordict('black')
            ),
            position
        )
        self.incontent.set_center(self.get_center())

    def copy_to(self, position: KindaType.Position2D):
        _obj = KindaTextBlock(
            self.text,
            self.fsize,
            self.surface.get_size(),
            position,
            self.dfcolor,
            self.detect,
            self.infactor
        )
        _obj.incontent = self.incontent._copy_to((0,0))
        _obj.incontent.set_center(_obj.get_center())
        _obj._set_color(self.color)
        _obj.set_state(self.state)
        return _obj


class KindaGrid(KindaBlock):

    def __init__(self, origin_block: KindaBlock, num_blocks: Tuple[int, int]):
        self.unit_block = origin_block
        _wu, _hu = origin_block.surface.get_size()
        _xu, _yu = _posu = origin_block.get_pos()
        self.hnum, self.vnum = _hnum, _vnum = num_blocks
        super(KindaGrid, self).__init__(
            (_wu*_hnum, _hu*_vnum),
            _posu,
            origin_block.dfcolor,
            origin_block.detect,
            origin_block.infactor
        )
        self.units = [
            [
                origin_block.copy_to(
                    (_xu+c*_wu, _yu+r*_hu)
                ) for r in range(_vnum)
            ] for c in range(_hnum)
        ]
        _borders = list()
        _rectg = self.rect
        _cnr_loop = _rectg.topleft, _rectg.topright, _rectg.bottomright, _rectg.bottomleft, _rectg.topleft
        for i in range(len(_cnr_loop)-1):
            _borders.append(
                (
                    pygame.Vector2(_cnr_loop[i]), 
                    pygame.Vector2(_cnr_loop[i+1])
                )
            )
        for r in range(1, _vnum):
            _borders.append(((_xu, _yu+r*_hu), (_xu+_hnum*_wu, _yu+r*_hu)))
        for c in range(1, _hnum):
            _borders.append(((_xu+c*_wu, _yu), (_xu+c*_wu, _yu+_vnum*_hu)))
        self.borders = _borders

    def draw_borders(self, screen: pygame.Surface, width:int=2, inner=True) -> None:
        for cnt, (i, f) in enumerate(self.borders):
            if cnt == 4:
                width = 1
                if not inner:
                    break
            pygame.draw.line(
                screen, 
                KindaColor.from_colordict('black'),
                i, 
                f, 
                width = width
            )

    def draw(self, screen:pygame.Surface, *indices:Tuple[int, int], border:bool=True) -> None:
        for xi, yi in indices:
            self.units[xi][yi].draw(screen)
        if border:
            self.draw_borders(screen)

    def draw_all(self, screen:pygame.Surface, border:bool=True, inner=True) -> None:
        for c in range(self.hnum):
            for r in range(self.vnum):
                self.units[c][r].draw(screen)
        if border:
            self.draw_borders(screen, inner=inner)

    def replace(
        self, 
        *ind_val_det_tuples:Tuple[Tuple[int, int], Union[None, str, KindaColor], bool]
        ) -> None:
        for (xi, yi), val, detect in ind_val_det_tuples:
            _block = self.units[xi][yi]
            if type(val) == str:
                _size = _block.surface.get_size()
                self.units[xi][yi] = KindaTextBlock(
                    val,
                    min(_size),
                    _size,
                    _block.get_pos(),
                    _block.dfcolor,
                    detect
                )
            else:
                self.units[xi][yi] = KindaBlock(
                    _block.surface.get_size(),
                    _block.get_pos(),
                    val if type(val)==KindaColor else _block.dfcolor,
                    detect
                ) 

    def block_index_at(self, position:KindaType.Position2D) -> Union[Tuple[int, int], None]:
        if not self.is_enclosing(position, boundary=True):
            return None
        _xrel, _yrel = pygame.Vector2(position) - self.get_pos()
        _w, _h = self.unit_block.surface.get_size()
        return int(_xrel//_w), int(_yrel//_h)


class KindaNonograms():

    CURRENT_MODE = 0
    MAIN = "m"
    HORIZONTAL = "h"
    VERTICAL = "v"
    IMAGE = "i"

    def __init__(
        self,
        position:KindaType.Position2D,
        num_mainblocks:Tuple[int, int],
        num_numblocks:Tuple[int, int],
        size_mainblock:Tuple[int, int],
        color_mainblock:KindaColor,
        color_numblock:KindaColor
        ):
        _szmw, _szmh = size_mainblock
        _nbmw, _nbmh = pygame.Vector2(num_mainblocks)
        _nbh, _nbv = pygame.Vector2(num_numblocks)
        _xi, _yi = _ipos = pygame.Vector2(position)
        _iw, _ih = _mshift = _nbv*_szmw, _nbh*_szmh
        if _iw%_nbmw!=0 or _ih%_nbmh!=0:
            raise Exception("Cannot initialize the image grid")
        self.grids = {
            KindaNonograms.MAIN: KindaGrid(
                KindaBlock(
                    size = size_mainblock,
                    position = _ipos + _mshift,
                    dfcolor = color_mainblock,
                    detect = True
                ),
                num_blocks = num_mainblocks
            ),
            KindaNonograms.HORIZONTAL: KindaGrid(
                KindaBlock(
                    size = size_mainblock,
                    position = ( int(_xi+_iw) , int(_yi) ),
                    dfcolor = color_numblock,
                    detect = False
                ),
                num_blocks = ( int(_nbmw) , int(_nbh) )
            ),
            KindaNonograms.VERTICAL: KindaGrid(
                KindaBlock(
                    size = size_mainblock,
                    position = ( int(_xi), int(_yi+_ih) ),
                    dfcolor = color_numblock,
                    detect = False
                ),
                num_blocks = ( int(_nbv) , int(_nbmh) )
            ),
            KindaNonograms.IMAGE: KindaGrid(
                KindaBlock(
                    size = ( int(_iw//_nbmw), int(_ih//_nbmh) ),
                    position = _ipos,
                    dfcolor = color_mainblock,
                    detect = False
                ),
                num_blocks = num_mainblocks
            )
        }
        self.history = list()

    def register(self, grid:str, numbers:Dict[int, List[int]]):
        _g = self.grids[grid]
        if grid == KindaNonograms.HORIZONTAL:
            for line, nlist in numbers.items():
                _maxlvl = _g.vnum - 1
                nlist.reverse()
                for level, num in enumerate(nlist):
                    _g.replace(
                        ( (line, _maxlvl-level) , str(num), True ) 
                    )
        elif grid == KindaNonograms.VERTICAL:
            for line, nlist in numbers.items():
                _maxlvl = _g.hnum - 1
                nlist.reverse()
                for level, num in enumerate(nlist):
                    _g.replace(
                        ( (_maxlvl-level, line) , str(num), True ) 
                    )
            
    def reset(self, screen:pygame.Surface) -> None:
        for key, grid in self.grids.items():
            for r in range(grid.hnum):
                for c in range(grid.vnum):
                    grid.units[r][c].set_state(KindaBlock.EMPTY)
                    grid.units[r][c].draw(screen)
            grid.draw_borders(screen, inner=not key==KindaNonograms.IMAGE)

    def record(self) -> None:
        pass

    def undo(self) -> None:
        pass

    def redo(self) -> None:
        pass

    def restart(self) -> None:
        pass


class KindaWindow():

    INITIALIZED = False
    EXIT = 'nomoreoptscuzreasons'

    screen: pygame.Surface

    @classmethod
    def init(cls):
        pygame.init()
        pygame.display.set_caption("KindaNonograms (by KindaOP)")
        cls.screen = pygame.display.set_mode((950, 950))
        cls.screen.fill(KindaColor.from_colordict('white'))
        cls.INITIALIZED = True
        _icon = pygame.Surface((32, 32))
        icon_grid = KindaGrid(
            KindaBlock(
                (8, 8),
                (0, 0),
                KindaColor.from_colordict('black'),
                detect = False
            ),
            (4, 4)
        )
        icon_grid.replace(
            ( (0,0) , KindaColor.from_colordict('white') , False ),
            ( (1,1) , KindaColor.from_colordict('white') , False ),
            ( (2,3) , KindaColor.from_colordict('red') , False ),
            ( (3,3) , KindaColor.from_colordict('green') , False ),
            ( (3,2) , KindaColor.from_colordict('blue') , False )
        )
        icon_grid.draw_all(_icon)
        pygame.display.set_icon(_icon)

    @classmethod
    def exit(cls):
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        sys.exit()

    def timer(ms: int) -> Callable:
        def timed_func(f) -> Callable:
            def loop(*args: Any, **kwargs: Any) -> None:
                end_time = time() + ms/1000
                finished = None
                finished = f(*args, **kwargs)
                while time() < end_time and finished == None:
                    pass
            return loop
        return timed_func

    def subpages(**subpages: Callable) -> Callable:
        def loop(f: Callable) -> Callable:
            def func(*args: Any, **kwargs: Any) -> None:
                while KindaWindow.INITIALIZED:
                    key = f(*args, **kwargs)
                    if key not in subpages.keys():
                        break
                    subpages[key]()
            return func
        return loop

    @classmethod
    @timer(7000)
    def closing_window(cls, *args, **kwargs) -> None:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        pygame.mixer.music.load(
            os.path.join(os.getcwd(), "Sounds", "closing.ogg")
        )
        pygame.mixer.music.play(loops=0)
        cls.screen.fill(KindaColor.from_colordict('blue'))
        pygame.display.flip()

    @classmethod
    def exit_prompt(cls, *args, **kwargs) -> str:
        pass

    @classmethod
    def import_game(cls, *args, **kwargs) -> str:
        pass

    @classmethod
    def history_window(cls, *args, **kwargs) -> str:
        return input("history: ")

    @classmethod
    def puzzle_window(cls, *args, **kwargs) -> str:
        buttons = {
            "fill": KindaGrid(
                KindaTextBlock(
                    "FILL",
                    50,
                    (150, 50),
                    (25, 25),
                    KindaColor.from_colordict('orange'),
                    detect = True
                ),
                (1, 1)
            ),
            "cross": KindaGrid(
                KindaTextBlock(
                    "CROSS",
                    50,
                    (150, 50),
                    (200, 25),
                    KindaColor.from_colordict('orange'),
                    detect = True
                ),
                (1, 1)
            ),
            "dot": KindaGrid(
                KindaTextBlock(
                    "DOT",
                    50,
                    (150, 50),
                    (375, 25),
                    KindaColor.from_colordict('orange'),
                    detect = True
                ),
                (1, 1)
            ),
            "clear": KindaGrid(
                KindaTextBlock(
                    "CLEAR",
                    50,
                    (150, 50),
                    (550, 25),
                    KindaColor.from_colordict('orange'),
                    detect = True
                ),
                (1, 1)
            ),
            "reset": KindaGrid(
                KindaTextBlock(
                    "RESET",
                    50,
                    (150, 50),
                    (725, 25),
                    KindaColor.from_colordict('orange'),
                    detect = True
                ),
                (1, 1)
            )
        }

        nng = KindaNonograms(
            position = (100, 100),
            num_mainblocks = (25, 25),
            num_numblocks = (7, 7),
            size_mainblock = (25, 25),
            color_mainblock = KindaColor.from_colordict('white'),
            color_numblock = KindaColor.from_colordict('yellow')
        )

        nng.register(
            KindaNonograms.HORIZONTAL,
            {
                0: [2],
                1: [1, 3],
                2: [2, 4],
                3: [2, 3, 1],
                4: [3, 2, 1],
                5: [4, 6, 6],
                6: [9, 3, 5],
                7: [15, 3, 1],
                8: [11, 3, 4],
                9: [5, 8, 3],
                10: [4, 3, 3, 1, 1],
                11: [2, 5, 3, 3],
                12: [6, 2, 3, 3],
                13: [2, 5, 2, 3, 3, 1, 1],
                14: [2, 5, 4, 3, 3],
                15: [1, 3, 1, 3, 3],
                16: [2, 7, 4, 1, 1],
                17: [15, 2, 1],
                18: [4, 3, 3, 4],
                19: [3, 6, 5],
                20: [2, 2, 2],
                21: [2, 2, 1],
                22: [1, 3, 1],
                23: [1, 4],
                24: [3]
            }
        )
        nng.register(
            KindaNonograms.VERTICAL,
            {
                0: [1],
                1: [3],
                2: [5, 2],
                3: [7, 1, 5],
                4: [6, 1, 5],
                5: [6, 2, 4],
                6: [5, 7],
                7: [13],
                8: [12],
                9: [4, 2, 2],
                10: [4, 1, 3],
                11: [5, 9],
                12: [1, 5, 2, 3],
                13: [1, 5, 1, 1, 1],
                14: [3, 6, 1, 1],
                15: [2, 1, 3, 4],
                16: [4, 4],
                17: [12],
                18: [10],
                19: [1, 6, 1],
                20: [5, 4],
                21: [7, 3, 3],
                22: [3, 15, 3],
                23: [3, 2, 2, 2, 2, 3, 2],
                24: [25]
            }
        )

        for button in buttons.values():
            button.draw_all(cls.screen, border=False)
        for key, grid in nng.grids.items():
            grid.draw_all(cls.screen, border=True, inner=not key==KindaNonograms.IMAGE)

        is_staying = True
        while is_staying:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_staying = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for key, button in buttons.items():
                        b = button.block_index_at(mouse_pos)
                        if b!= None:
                            if key == "fill":
                                KindaNonograms.CURRENT_MODE = KindaBlock.FILLED
                            elif key == "cross":
                                KindaNonograms.CURRENT_MODE = KindaBlock.CROSSED
                            elif key == "dot":
                                KindaNonograms.CURRENT_MODE = KindaBlock.DOTTED
                            elif key == "clear":        
                                KindaNonograms.CURRENT_MODE = KindaBlock.EMPTY
                            elif key == "reset":
                                nng.reset(cls.screen)
                            button.draw_borders(cls.screen, width=5)
                            continue
                        button.draw_all(cls.screen, border=False)
                    for key, grid in nng.grids.items():
                        b = grid.block_index_at(mouse_pos)
                        if b != None:
                            xi, yi = b
                            if key == KindaNonograms.MAIN:
                                main = grid.units[xi][yi]
                                img = nng.grids[KindaNonograms.IMAGE].units[xi][yi]
                                if main.state == KindaNonograms.CURRENT_MODE:
                                    main.set_state(KindaBlock.EMPTY)
                                    img.set_state(KindaBlock.EMPTY)
                                else:
                                    main.set_state(KindaNonograms.CURRENT_MODE, KindaColor.from_colordict('black'))
                                    _imgmode = KindaBlock.EMPTY if KindaNonograms.CURRENT_MODE != KindaBlock.FILLED else KindaNonograms.CURRENT_MODE
                                    img.set_state(_imgmode, KindaColor.from_colordict('black'))
                                main.draw(cls.screen)
                                img.draw(cls.screen)
                            elif key == KindaNonograms.HORIZONTAL or key == KindaNonograms.VERTICAL:
                                nblock = nng.grids[key].units[xi][yi]
                                _nummode = KindaBlock.CROSSED if nblock.state != KindaBlock.CROSSED else KindaBlock.EMPTY
                                nblock.set_state(_nummode)
                                nblock.draw(cls.screen)
                        grid.draw_borders(cls.screen, inner=not key==KindaNonograms.IMAGE)
                        
                pygame.display.flip()

    @classmethod
    def tutorial_window(cls, *args, **kwargs) -> str:
        pass

    @classmethod
    @subpages(
        opt1=puzzle_window
    )
    def puzzle_menu(cls, *args, **kwargs) -> str:
        return input("puzzle menu: ")

    @classmethod
    @subpages(
        opt1=puzzle_menu,
        opt2=history_window,
        opt3=import_game
    )
    def start_menu(cls, *args, **kwargs) -> str:
        pygame.mixer.music.load(
            os.path.join(os.getcwd(), "Sounds", "opening.ogg")
        )
        pygame.mixer.music.play(loops=0)
        pygame.mixer.music.set_endevent(KindaEvent.MUSIC_END)


        buttons = {
            "puzzle": KindaGrid(
                KindaTextBlock(
                    "PUZZLE",
                    50,
                    (300, 50),
                    (100, 100),
                    KindaColor.random(),
                    detect = True
                ),
                (1, 1)
            )
        }
        cls.screen.fill(KindaColor.random())
        pygame.time.set_timer(KindaEvent.BG_CHANGE, millis=200, loops=5)
        
        is_staying = True
        while is_staying:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_staying = False
                elif event.type == KindaEvent.MUSIC_END:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                    pygame.mixer.music.load(
                        os.path.join(os.getcwd(), "Sounds", "looping.ogg")
                    )
                    pygame.mixer.music.play(loops=-1)
                    pygame.mixer.music.set_endevent()
                    for _, button in buttons.items():
                        button.draw_all(cls.screen)
                elif event.type == KindaEvent.BG_CHANGE:
                    cls.screen.fill(KindaColor.random())

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    b = button.block_index_at(pygame.mouse.get_pos())
                    print(b)
                    if b != None:
                        return "optlol"
                
                pygame.display.flip()
        pygame.time.set_timer(KindaEvent.BG_CHANGE, 0)

    @classmethod
    def opening_window(cls, *args, **kwargs) -> None:
        opening_gif = KindaGIF(
            os.path.join(os.getcwd(), "Images", "interesting.gif"),
            period = 1,
            position = (100, 100)
        )
        # pbar = Block((400, 100), (100, 700),
        #              dfcolor=THECOLORS['red'], interactable=True)
        for i in range(100):
            opening_gif.step(reversed=True)
            opening_gif.draw(cls.screen)
            pygame.display.flip()
            pygame.time.delay(70)


def main():
    KindaWindow.init()
    KindaWindow.opening_window()
    KindaWindow.start_menu()
    KindaWindow.puzzle_window()
    KindaWindow.closing_window()
    KindaWindow.exit()

if __name__ == "__main__":
    main()
