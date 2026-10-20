
from typing import Callable

import binascii
import importlib.resources


class RainbowTable:
    _crc32_table: dict[int, str] | None

    def __init__(self):
        self._crc32_table = None

    def crc32(self, hash: int) -> str | None:
        if self._crc32_table is None:
            self._crc32_table = self._generate(binascii.crc32)
        return self._crc32_table.get(hash)

    def _generate(self, func: Callable[[bytes], int]) -> dict[int, str]:
        table = {}
        for word in self._load_wordlist():
            table[func(word.encode())] = word
        return table

    def _load_wordlist(self) -> list[str]:
        file = \
            importlib.resources.files("jungle").joinpath("files/wordlist.txt")
        return file.read_text().splitlines()
    

table = RainbowTable()


def crc32(hash: int) -> str | None:
    return table.crc32(hash)
