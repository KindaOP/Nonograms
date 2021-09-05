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
import platform
from PIL import Image
from typing import Any, Callable, Dict, List, Union, Tuple


class KType():
    Pos2D = Union[Tuple[int, int], pygame.Vector2]

    class Float01(float):
        def __new__(cls, x=1, *args, **kwargs):
            obj = super(cls).__new__(cls, x, *args, **kwargs)
            if obj < 0 or obj > 1:
                raise ValueError("the value must be within [0,1]")


class KColor(pygame.Color):
    def __init__(self, r:int, g:int, b:int, a:int):
        super(KColor, self).__init__(r, g, b, a)

    @classmethod
    def name(cls, clrname:str):
        return cls(*THECOLORS[clrname])

    @classmethod
    def random(cls, alpha:Union[int, None]=255):
        return cls(
            random.randint(0,255),
            random.randint(0,255),
            random.randint(0,255),
            random.randint(0,255) if alpha==None else alpha
        )

    @classmethod
    def random_binary(cls, alpha:Union[int, None]=255):
        _val = 255 * random.randint(0,1)
        return cls(
            _val, 
            _val, 
            _val, 
            random.randint(0,255) if alpha==None else alpha
        )

    def invert(self, alpha:bool=False):        
        return KColor(
            255 - self.r,
            255 - self.g,
            255 - self.b,
            255 - self.a if alpha else self.a
        )


class KObject():
    def __init__(
        self, 
        screen:pygame.Surface, 
        surface:pygame.Surface,
        position:KType.Pos2D
        ):
        self.screen = screen
        self.surface = surface
        self.rect = pygame.Rect(*position, *surface.get_size())

    def draw(self) -> None:
        self.screen.blit(self.surface, self.rect)

    def get_position(self) -> pygame.Vector2:
        return pygame.Vector2(self.rect.topleft)

    def set_position(self, destination:Union[KType.Pos2D, None]) -> None:
        self.rect.move_ip(
            pygame.Vector2(destination) - self.get_position()
        )

    def get_center(self) -> pygame.Vector2:
        return pygame.Vector2(self.rect.center)

    def set_center(self, destination:Union[KType.Pos2D, None]) -> None:
        self.rect.move_ip(
            pygame.Vector2(destination) - self.get_center()
        )

    def is_enclosing(
        self,
        position:KType.Pos2D,
        boundary:bool = True
        ) -> bool:
        _x, _y = position
        if boundary:
            return _x >= self.rect.left and _x <= self.rect.right \
                and _y >= self.rect.top and _y <= self.rect.bottom
        else:
            return _x > self.rect.left and _x < self.rect.right \
                and _y > self.rect.top and _y < self.rect.bottom

    def copy(self, destination:Union[KType.Pos2D, None]):
        newobj = KObject(
            self.screen,
            self.surface,
            self.get_position() if destination is None else destination
        )
        return newobj


class KGIF(KObject):
    def __init__(
        self,
        screen:pygame.Surface,
        position:KType.Pos2D,
        fpath:str = os.getcwd(),
        Ts:int = 1
        ):
        self.frames = list()
        self.cframe = 0
        def add_pyimage(frames:list, img:Image) -> None:
            _img = img.convert('RGBA')
            frames.append(
                pygame.image.fromstring(
                    _img.tobytes(),
                    _img.size,
                    _img.mode
                ).convert_alpha()
            )
            return
        with Image.open(fpath) as image:
            add_pyimage(self.frames, image)
            super(KGIF, self).__init__(screen, self.frames[0], position)
            while True:
                try:
                    image.seek(image.tell()+Ts)
                except EOFError:
                    break
                else:
                    add_pyimage(self.frames, image)
                
    def step(self, step:int=1, backward:bool=False) -> None:
        if backward:
            _next = self.cframe - step
            self.cframe = _next if _next>=0 else len(self.frames) - 1
        else:
            _next = self.cframe + step
            self.cframe = _next if _next<len(self.frames) else 0
        self.surface = self.frames[self.cframe]

    def get(
        self,
        n:Union[int, None] = None,
        position:Union[KType.Pos2D, None] = None
        ) -> KObject:
        _n = n if n is not None else self.cframe
        _pos = position if position is not None else self.get_position()
        return KObject(self.screen, self.frames[_n], _pos)

    # Overridden
    def copy(): pass


class KBlock(KObject):
    EMPTY = 0
    FILLED = 1
    DOTTED = 2
    CROSSED = 3
    CHECKED = 4

    def __init__(
        self,
        screen:pygame.Surface,
        size:Tuple[int, int],
        position:KType.Pos2D,
        color_default:KColor = KColor.name('white'),
        clickable:bool = False,
        inner_factor:KType.Float01 = 0.8
        ):
        super(KBlock, self).__init__(
            screen, pygame.Surface(size), position
        )
        self.color_default = color_default
        self.surface.fill(color_default)
        self.color = color_default
        self.state = KBlock.EMPTY
        self.clickable = clickable
        self.inner_factor = inner_factor
        self.inner_cross = KObject(
            screen,
            pygame.Surface(
                tuple(int(inner_factor*dim) for dim in size)
            ),
            position
        )
        self.inner_cross.set_center(self.get_center())
        self.inner_dot = KObject(
            screen,
            pygame.Surface(
                tuple(int((1-inner_factor)*dim) for dim in size)
            ),
            position
        )
        self.inner_dot.set_center(self.get_center())
        self.inner_object = None

    # Overridden
    def draw(self, clr:Union[KColor, None]=None) -> None:
        def clear():
            self.color = self.color_default
            self.surface.fill(self.color)
            super(KBlock, self).draw()
            if self.inner_object is not None:
                self.inner_object.draw()
            return
        if self.state == KBlock.EMPTY:
            clear()
        elif self.state == KBlock.FILLED:
            self.color = self.color if clr is None else clr 
            self.surface.fill(self.color)
            super(KBlock, self).draw()
        elif self.state == KBlock.CROSSED:
            clear()
            _rect = self.inner_cross.rect
            pygame.draw.line(
                self.screen,
                self.color_default if clr is None else clr,
                _rect.topleft,
                _rect.bottomright,
                width = 3
            )
            pygame.draw.line(
                self.screen,
                self.color_default if clr is None else clr,
                _rect.bottomleft,
                _rect.topright,
                width = 3
            )
        elif self.state == KBlock.DOTTED:
            clear()
            self.inner_dot.draw()
        elif self.state == KBlock.CHECKED:
            clear()
            _rect = self.inner_cross.rect
            pygame.draw.line(
                self.screen,
                self.color_default if clr is None else clr,
                _rect.bottomleft,
                _rect.topright
            )

    # Overridden
    def copy(self, destination:Union[KType.Pos2D, None]=None):
        newobj = KBlock(
            self.screen,
            self.rect.size,
            self.get_position() if destination is None else destination,
            self.color_default,
            self.clickable,
            self.inner_factor
        )
        newobj.color = self.color
        newobj.state = self.state
        return newobj


class KTextBlock(KBlock):
    def __init__(
        self,
        screen:pygame.Surface,
        text:str,
        font_size:int,
        size:Tuple[int, int],
        position:KType.Pos2D,
        color_text:KColor = KColor.name('black'),
        color_default:KColor = KColor.name('white'),
        clickable:bool = False,
        inner_factor:KType.Float01 = 0.8,
        is_centered:bool = True
        ):
        super(KTextBlock, self).__init__(
            screen, 
            size, 
            position, 
            color_default, 
            clickable, 
            inner_factor
        )
        self.text = text
        self.font_size = font_size
        self.color_text = color_text
        self.is_centered = is_centered
        self.inner_object = KObject(
            screen,
            pygame.font.Font.render(
                pygame.font.SysFont(
                    pygame.font.get_default_font(),
                    font_size
                ),
                text,
                True,
                color_text
            ),
            position
        )
        if is_centered:
            self.inner_object.set_center(self.get_center())

    # Overridden
    def draw(self, clr:Union[KColor, None]=None) -> None:
        if self.state == KBlock.FILLED:
            raise ValueError("textblocks cannot have FILLED state")
        super(KTextBlock, self).draw(clr)

    # Overridden
    def copy(self, destination:Union[KType.Pos2D, None]=None):
        newobj = KTextBlock(
            self.screen,
            self.text,
            self.font_size,
            self.rect.size,
            self.rect.topleft if destination is None else destination,
            self.color_text,
            self.color_default,
            self.clickable,
            self.inner_factor
        )
        newobj.color = self.color
        newobj.state = self.state
        return newobj


class KGrid(KObject):
    def __init__(
        self,
        unit_origin:KBlock,
        num_blocks:Tuple[int, int]
        ):
        self.unit_origin = unit_origin
        self.num_blocks = _hnum, _vnum = num_blocks
        _wu, _hu = unit_origin.rect.size
        _xu, _yu = _posu = unit_origin.get_position()
        super(KGrid, self).__init__(
            unit_origin.screen,
            pygame.Surface((_wu*_hnum, _hu*_vnum)),
            _posu,
        )
        self.unit_array = [[unit_origin.copy(
            (_xu+c*_wu, _yu+r*_hu)
        ) for r in range(_vnum)] for c in range(_hnum)]
        _cnr_loop = (
            self.rect.topleft,
            self.rect.topright,
            self.rect.bottomright,
            self.rect.bottomleft,
            self.rect.topleft
        )
        self.border_outer = list((
            _cnr_loop[i], _cnr_loop[i+1]
        ) for i in range(len(_cnr_loop)-1) )
        self.border_inner = list()
        for r in range(1, _vnum):
            self.border_inner.append((
                (_xu, _yu+r*_hu), (_xu+_hnum*_wu, _yu+r*_hu)
            ))
        for c in range(1, _hnum):
            self.border_inner.append((
                (_xu+c*_wu, _yu), (_xu+c*_wu, _yu+_vnum*_hu)
            ))

    def draw_borders(self, bdin:bool=True, bdout:bool=True) -> None:
        if bdin:
            for i, f in self.border_inner:
                pygame.draw.line(
                    self.screen, KColor.name('black'), i, f, 1
                )
        if bdout:
            for i, f in self.border_outer:
                pygame.draw.line(
                    self.screen, KColor.name('black'), i, f, 3
                )

    # Overridden
    def draw(
        self,
        *indices:Tuple[int, int],
        bdin:bool = True,
        bdout:bool = True
        ):
        for xi, yi in indices:
            self.unit_array[xi][yi].draw()
        self.draw_borders(bdin, bdout)

    def draw_all(self, bdin:bool=True, bdout:bool=True) -> None:
        _hnum, _vnum = self.num_blocks
        for c in range(_hnum):
            for r in range(_vnum):
                self.unit_array[c][r].draw()
        self.draw_borders(bdin, bdout)

    def replace(
        self,
        *ind_block_tuples:Tuple[Tuple[int, int], KBlock]
        ) -> None:
        for (xi, yi), block in ind_block_tuples:
            self.unit_array[xi][yi] = block

    def block_index_at(
        self, 
        position:KType.Pos2D
        ) -> Union[Tuple[int, int], None]:
        if not self.is_enclosing(position):
            return None
        _xrel, _yrel = pygame.Vector2(position)- self.get_position()
        _w, _h = self.unit_origin.rect.size
        return int(_xrel//_w), int(_yrel//_h)

    # Overridden
    def set_position(): pass

    #Overridden
    def set_center(): pass

    # Overridden
    def copy(): pass


class KButton(KTextBlock):
    def __init__(
        self,
        screen:pygame.Surface,
        text:str,
        size:Tuple[int, int],
        position:KType.Pos2D,
        color_text:KColor,
        color_default:KColor,
        on_pressed:Callable,
        on_released:Union[Callable, None] = None,
        color_bp:KColor = KColor.name('white'),
        color_br:KColor = KColor.name('black')
        ):
        super(KButton, self).__init__(
            screen,
            text,
            min(size),
            size,
            position,
            color_text,
            color_default,
            clickable = True
        )
        self.on_pressed = on_pressed
        self.on_released = on_released
        self.is_pressed = False
        self.color_bp = color_bp
        self.color_br = color_br
        _cnr_loop = (
            self.rect.topleft,
            self.rect.topright,
            self.rect.bottomright,
            self.rect.bottomleft,
            self.rect.topleft
        )
        self.border = list((
            _cnr_loop[i], _cnr_loop[i+1]
        ) for i in range(len(_cnr_loop)-1) )      

    # Overridden
    def draw(self):
        super(KButton, self).draw()
        _clr = self.color_bp if self.is_pressed else self.color_br
        for i, f in self.border:
            pygame.draw.line(
                self.surface, _clr, i, f, 3
            )

    def toggle(self, t_f:Union[bool, None]=None) -> None:
        self.clickable = not self.clickable if t_f is None else t_f

    def check(
        self, 
        mouse_position:KType.Pos2D, 
        *args, **kwargs
        ) -> Tuple[bool, Any]:
        if not self.is_enclosing(mouse_position) or not self.clickable:
            return False, None
        _pressed = self.is_pressed
        self.is_pressed = not _pressed and self.on_released is not None
        onclick = self.on_released if _pressed else self.on_pressed
        value = onclick(*args, **kwargs)
        return True, value

    def press(self, *args, **kwargs) -> Any:
        self.is_pressed = self.on_released is not None
        return self.on_pressed(*args, **kwargs)

    def release(self, *args, **kwargs) -> Any:
        if self.on_released is None:
            raise NotImplementedError("the button has no on_released")
        self.is_pressed = False
        return self.on_released(*args, **kwargs)

    # Overridden
    def copy(): pass


class KProgressBar(KObject):
    def __init__(
        self,
        screen:pygame.Surface,
        size:Tuple[int, int],
        position:KType.Pos2D,
        progress:KType.Float01 = 1,
        color_bar:KColor = KColor.name('white'),
        color_progress:KColor = KColor.name('black'),
        color_pfg:KColor = KColor.name('black'),
        color_pbg:KColor = KColor.name('white')
        ):
        super(KProgressBar, self).__init__(
            screen, pygame.Surface(size), position
        )
        self.progress = progress
        self.color_bar = color_bar
        self.color_progress = color_progress
        self.color_pfg = color_pfg
        self.color_pbg = color_pbg
        _w, _h = self.rect.size
        _x, _y = position
        _bw = _w-2*_h
        self.bar = KBlock(screen, (_bw, _h), position, color_bar)
        self.progress = KBlock(
            screen, (int(progress*_bw), _h), position, color_progress
        )
        self.percent = KTextBlock(
            screen, 
            f"{str(int(progress*100))}%", 
            _h,
            (2*_h, _h),
            (_x+_bw, _y),
            color_pfg,
            color_pbg
        )

    # Overridden
    def draw(self) -> None:
        self.bar.draw()
        self.progress.draw()
        self.percent.draw()

    def set_progress(self, progress:KType.Float01) -> None:
        _w, _h = self.rect.size
        _x, _y = self.get_position()
        _bw = self.bar.rect.size[0]
        self.progress = KBlock(
            self.screen, 
            (int(progress*_bw), _h), 
            self.get_position(), 
            self.color_progress
        )
        self.percent = KTextBlock(
            self.screen, 
            f"{str(int(progress*100))}%", 
            _h,
            (2*_h, _h),
            (_x+_bw, _y),
            self.color_pfg,
            self.color_pbg
        )

    # Overridden
    def set_position(self, destination: Union[KType.Pos2D, None]) -> None:
        _des = pygame.Vector2(destination)
        _shift = _des - self.get_position()
        super().set_position(_des)
        self.bar.rect.move_ip(*_shift)
        self.progress.rect.move_ip(*_shift)
        self.percent.rect.move_ip(*_shift)

    # Overridden
    def set_center(self, destination: Union[KType.Pos2D, None]) -> None:
        _des = pygame.Vector2(destination)
        _shift = _des - self.get_center()
        super().set_center(destination)
        self.bar.rect.move_ip(*_shift)
        self.progress.rect.move_ip(*_shift)
        self.percent.rect.move_ip(*_shift)

    # Overridden
    def copy(): pass


class KNonograms(KObject):
    MAIN = 0
    HORIZONTAL = 1
    VERTICAL = 2
    IMAGE = 3

    def __init__(
        self,
        screen:pygame.Surface,
        position:KType.Pos2D,
        num_mainblocks:Tuple[int, int],
        num_numblocks:Tuple[int, int],
        size_mainblock:Tuple[int ,int],
        color_mainblocks:KColor,
        color_numblocks:KColor
        ):
        _szmw, _szmh = size_mainblock
        _nbmw, _nbmh = num_mainblocks
        _nbh, _nbv = num_numblocks
        _iw, _ih = _mshift = pygame.Vector2(_nbv*_szmw, _nbh*_szmh)
        if _iw%_nbmw!=0 or _ih%_nbmh!=0:
            raise Exception("Cannot initialize the image grid")
        super(KNonograms, self).__init__(
            screen,
            pygame.Surface((_iw+_nbmw*_szmw, _ih+_nbmh*_szmh)),
            position
        )
        _xi, _yi = self.get_position()
        self.grids = {
            KNonograms.MAIN: KGrid(
                KBlock(
                    screen = screen,
                    size = size_mainblock,
                    position = _mshift + self.get_position(),
                    color_default = color_mainblocks,
                    clickable = True
                ),
                num_blocks = num_mainblocks
            ),
            KNonograms.HORIZONTAL: KGrid(
                KBlock(
                    screen = screen,
                    size = size_mainblock,
                    position = ( int(_xi+_iw) , int(_yi) ),
                    color_default = color_numblocks,
                    clickable = False
                ),
                num_blocks = ( int(_nbmw) , int(_nbh) )
            ),
            KNonograms.VERTICAL: KGrid(
                KBlock(
                    screen = screen,
                    size = size_mainblock,
                    position = ( int(_xi), int(_yi+_ih) ),
                    color_default = color_numblocks,
                    clickable = False
                ),
                num_blocks = ( int(_nbv) , int(_nbmh) )
            ),
            KNonograms.IMAGE: KGrid(
                KBlock(
                    screen = screen,
                    size = ( int(_iw//_nbmw), int(_ih//_nbmh) ),
                    position = self.get_position(),
                    color_default = color_mainblocks,
                    clickable = False
                ),
                num_blocks = num_mainblocks
            )
        }
        self.history = list()

    # Overridden
    def draw(self, *gnums:int) -> None:
        for gnum in gnums:
            self.grids[gnum].draw_all()

    # Overridden
    def draw_all(self) -> None:
        for grid in self.grids.values():
            grid.draw_all()

    def register_h(
        self, 
        line_numbers_dict:Dict[int, List[int]]
        ) -> None:
        _g = self.grids[KNonograms.HORIZONTAL]
        _gu = _g.unit_origin
        _maxlvl = _g.num_blocks[1] - 1
        for line, nlist in line_numbers_dict.items():
            for level, num in enumerate(nlist[::-1]):
                _g.replace((
                    (line, _maxlvl-level),
                    KTextBlock(
                        _g.screen,
                        str(num),
                        min(_gu.rect.size),
                        _gu.rect.size,
                        _gu.get_position(),
                        _gu.color_default,
                        clickable = True
                    )
                ))

    def register_v(
        self, 
        line_numbers_dict:Dict[int, List[int]]
        ) -> None:
        _g = self.grids[KNonograms.VERTICAL]
        _gu = _g.unit_origin
        _maxlvl = _g.num_blocks[0] - 1
        for line, nlist in line_numbers_dict.items():
            for level, num in enumerate(nlist[::-1]):
                _g.replace((
                    (_maxlvl-level, line),
                    KTextBlock(
                        _g.screen,
                        str(num),
                        min(_gu.rect.size),
                        _gu.rect.size,
                        _gu.get_position(),
                        _gu.color_default,
                        clickable = True
                    )
                ))

    def record():
        pass

    def reset(self) -> None:
        for key, grid in self.grids.items():
            _hnum, _vnum = grid.num_blocks
            for c in range(_hnum):
                for r in range(_vnum):
                    grid.unit_array[c][r].state = KBlock.EMPTY
            grid.draw_all(bdin=not key==KNonograms.IMAGE)

    def undo():
        pass

    def redo():
        pass

    def restart():
        pass

    # Overridden
    def set_position(): pass

    # Overridden
    def set_center(): pass

    # Overridden
    def copy(): pass


class KWindow():
    MUSIC_END = pygame.USEREVENT + 1
    BG_CHANGE = pygame.USEREVENT + 2

    EXIT = 'exit'
    _INITIALIZED = False
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
            # pygame.mixer.music.stop()
            # pygame.mixer.music.unload()
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
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            self.clock.tick(self.fps)
            pbar.set_progress((i+1)/n_frames)
            pbar.draw()
            opening_gif.draw()
            opening_gif.step()
            pygame.display.flip()
            pygame.time.delay(50)
        pygame.time.delay(1000)

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
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page = KWindow.EXIT
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
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page = KWindow.EXIT
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
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page == "closing_window"
            pygame.display.flip()
        return target_page

    def import_game(self):
        print("import_game")
        target_page = str()
        while not target_page:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page == "closing_window"
            pygame.display.flip()
        return target_page

    def exit_prompt():
        print("exit_prompt")
        target_page = str()
        while not target_page:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    target_page == KWindow.EXIT
            pygame.display.flip()
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
        is_staying = True
        while is_staying:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_staying = False
                elif event.type == KWindow.MUSIC_END:
                    is_staying = False

    def run(self) -> None:
        self.opening_window()
        while self.current_page != KWindow.EXIT:
            self.current_page = eval(
                "".join(["self.", self.current_page, "()"])
            )
        self.closing_window()


def main():
    KWindow().run()


if __name__ == '__main__':
    main()
