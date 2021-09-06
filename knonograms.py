import pygame

from typing import Tuple, Dict, List

from pygame import mouse

from kauxiliaries import KType, KColor
from kobjects import KObject, KBlock, KTextBlock, KGrid


class KNonograms(KObject):
    MAIN = 0
    HORIZONTAL = 1
    VERTICAL = 2
    IMAGE = 3
    CURRENT_MODE = KBlock.EMPTY

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
        for key, grid in self.grids.items():
            grid.draw_all(bdin=not key == KNonograms.IMAGE)

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

    def scm(self, mode:int) -> None:
        KNonograms.CURRENT_MODE = mode

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

    def check(
        self, 
        mouse_position:KType.Pos2D,
        *args, **kwargs
        ) -> bool:
        for key, grid in self.grids.items():
            if not grid.is_enclosing(mouse_position) or key==KNonograms.IMAGE:
                return False
            xi, yi = grid.block_index_at(mouse_position)
            _g = grid.unit_array[xi][yi]
            if not _g.clickable:
                return False
            _g.state = KNonograms.CURRENT_MODE
            _g.draw(clr=KColor.name('black'))
            grid.draw_borders()
            _gi = self.grids[KNonograms.IMAGE].unit_array[xi][yi]
            _gi.state = KNonograms.CURRENT_MODE
            _gi.draw(clr=KColor.name('black'))
            self.grids[KNonograms.IMAGE].draw_borders(bdin=False)
            return True

    # Overridden
    def copy(): pass
