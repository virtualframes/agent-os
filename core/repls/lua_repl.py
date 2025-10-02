"""Lua REPL implementation."""
from __future__ import annotations

from .base import BaseREPL


class LuaREPL(BaseREPL):
    language = "lua"

    def __init__(self) -> None:
        super().__init__(prompt="> ")

    @property
    def command(self) -> str:
        return "lua"


__all__ = ["LuaREPL"]
