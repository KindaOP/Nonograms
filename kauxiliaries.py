import pygame
from pygame.colordict import THECOLORS

import random
from typing import Union, Tuple, Dict, List


class KType():
    Pos2D = Union[Tuple[int, int], pygame.Vector2]
    Puzzle = Tuple[Dict[int, List[int]], Dict[int, List[int]]]

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