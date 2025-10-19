from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    menadzer = "MENADZER"
    sef = "SEF"
    komercijalista = "KOMERCIJALISTA"
    magacioner = "MAGACIONER"
    
    @classmethod
    def _missing_(cls, value):
        """Case-insensitive lookup"""
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None
