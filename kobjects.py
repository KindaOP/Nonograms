import pygame
import pygame.draw
import pygame.font
import pygame.image

import os
from PIL import Image
from typing import Union, Tuple, Callable, Any

from kauxiliaries import KType, KColor


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
                _rect.topright,
                width = 3
            )

    # Overridden
    def set_position(self, destination: Union[KType.Pos2D, None]) -> None:
        super(KBlock, self).set_position(destination)
        self.inner_cross.set_position(destination)
        self.inner_dot.set_position(destination)

    # Overridden
    def set_center(self, destination: Union[KType.Pos2D, None]) -> None:
        super(KBlock, self).set_center(destination)
        self.inner_cross.set_center(destination)
        self.inner_dot.set_center(destination)

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
    def set_position(self, destination: Union[KType.Pos2D, None]) -> None:
        super(KTextBlock, self).set_position(destination)
        if self.is_centered:
            self.inner_object.set_center(self.get_center())
        else:
            self.inner_object.set_position(self.get_position())

    # Overridden
    def set_center(self, destination: Union[KType.Pos2D, None]) -> None:
        super(KTextBlock, self).set_center(destination)
        if self.is_centered:
            self.inner_object.set_center(self.get_center())
        else:
            self.inner_object.set_position(self.get_position())

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
        font_size:int,
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
            font_size,
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
            return False, str()
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