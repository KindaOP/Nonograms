import pygame

from typing import Tuple

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
        self.pih = -1

    # Overridden
    def draw(self, *gnums:int) -> None:
        for gnum in gnums:
            self.grids[gnum].draw_all()

    # Overridden
    def draw_all(self) -> None:
        for key, grid in self.grids.items():
            grid.draw_all(bdin=not key == KNonograms.IMAGE)

    def register(self, puzzle:KType.Puzzle) -> None:
        hdict, vdict = puzzle
        _g = self.grids[KNonograms.HORIZONTAL]
        _gu = _g.unit_origin
        _maxlvl = _g.num_blocks[1] - 1
        for line, nlist in hdict.items():
            for level, num in enumerate(nlist[::-1]):
                xi, yi = line, _maxlvl-level
                _g.replace((
                    (xi, yi),
                    KTextBlock(
                        _g.screen,
                        str(num),
                        min(_gu.rect.size),
                        _gu.rect.size,
                        _g.unit_array[xi][yi].get_position(),
                        KColor.name('black'),
                        _gu.color_default,
                        clickable = True
                    )
                ))
        _g = self.grids[KNonograms.VERTICAL]
        _gu = _g.unit_origin
        _maxlvl = _g.num_blocks[0] - 1
        for line, nlist in vdict.items():
            for level, num in enumerate(nlist[::-1]):
                xi, yi = _maxlvl-level, line
                _g.replace((
                    (xi, yi),
                    KTextBlock(
                        _g.screen,
                        str(num),
                        min(_gu.rect.size),
                        _gu.rect.size,
                        _g.unit_array[xi][yi].get_position(),
                        KColor.name('black'),
                        _gu.color_default,
                        clickable = True
                    )
                ))

    def scm(self, mode:int) -> None:
        KNonograms.CURRENT_MODE = mode

    def _clear(self) -> None:
        for key, grid in self.grids.items():
            _hnum, _vnum = grid.num_blocks
            for c in range(_hnum):
                for r in range(_vnum):
                    grid.unit_array[c][r].state = KBlock.EMPTY
            grid.draw_all(bdin=not key==KNonograms.IMAGE)

    def reset(self) -> None:
        self._clear()
        if self.pih != len(self.history)-1:
            self.history = self.history[:self.pih+1] 
        self.history.append(self.pih)
        self.pih += 1

    def undo(self) -> None:
        if self.pih >= 0:
            _history = self.history[self.pih]
            if type(_history) is int:
                self._clear()
                for _tpih in range(_history+1):
                    print(_tpih)
                    key, (xi, yi), (_, state) = self.history[_tpih]
                    _g = self.grids[key].unit_array[xi][yi]
                    _g.state = state
                    _g.draw(clr=KColor.name('black'))
                    self.grids[key].draw_borders()
                    if key == KNonograms.MAIN:
                        _gi = self.grids[KNonograms.IMAGE].unit_array[xi][yi]
                        _gi.state = state
                        _gi.draw(clr=KColor.name('black'))
                        self.grids[KNonograms.IMAGE].draw_borders(bdin=False)
                self.pih -= 1
                return
            key, (xi, yi), (state, _) = _history
            _g = self.grids[key].unit_array[xi][yi]
            _g.state = state
            _g.draw(clr=KColor.name('black'))
            self.grids[key].draw_borders()
            if key == KNonograms.MAIN:
                _gi = self.grids[KNonograms.IMAGE].unit_array[xi][yi]
                _gi.state = state
                _gi.draw(clr=KColor.name('black'))
                self.grids[KNonograms.IMAGE].draw_borders(bdin=False)
            self.pih -= 1

    def redo(self) -> None:
        if self.pih+1 < len(self.history):
            _history = self.history[self.pih+1]
            if type(_history) is int:
                self._clear()
                self.pih += 1
                return
            key, (xi, yi), (_, state) = _history
            _g = self.grids[key].unit_array[xi][yi]
            _g.state = state
            _g.draw(clr=KColor.name('black'))
            self.grids[key].draw_borders()
            if key == KNonograms.MAIN:
                _gi = self.grids[KNonograms.IMAGE].unit_array[xi][yi]
                _gi.state = state
                _gi.draw(clr=KColor.name('black'))
                self.grids[KNonograms.IMAGE].draw_borders(bdin=False)
            self.pih += 1

    def restart(self):
        pass

    def check(
        self, 
        mouse_position:KType.Pos2D,
        *args, **kwargs
        ) -> bool:
        if not self.is_enclosing(mouse_position):
            return False
        for key, grid in self.grids.items():
            if not grid.is_enclosing(mouse_position) or key==KNonograms.IMAGE:
                continue
            xi, yi = ind = grid.block_index_at(mouse_position)
            _g = grid.unit_array[xi][yi]
            if not _g.clickable:
                return False
            _state = _g.state
            if key == KNonograms.MAIN:
                _g.state = KNonograms.CURRENT_MODE
                _g.draw(clr=KColor.name('black'))
                grid.draw_borders()
                gridi = self.grids[KNonograms.IMAGE]
                _gi = gridi.unit_array[xi][yi]
                _gi.state = _g.state if _g.state==KBlock.FILLED else KBlock.EMPTY
                _gi.draw(clr=KColor.name('black'))
                gridi.draw_borders(bdin=False)
            else:
                _g.state = KBlock.CROSSED if _g.state==KBlock.EMPTY else KBlock.EMPTY
                _g.draw(clr=KColor.name('black'))
                grid.draw_borders()
            if self.pih != len(self.history)-1:
                self.history = self.history[:self.pih+1] 
            self.history.append((key, ind, (_state, _g.state)))
            self.pih += 1
            return True
        return False

    # Overridden
    def copy(): pass
