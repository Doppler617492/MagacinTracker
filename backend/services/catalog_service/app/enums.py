from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    menadzer = "menadzer"
    sef = "sef"
    komercijalista = "komercijalista"
    magacioner = "magacioner"
