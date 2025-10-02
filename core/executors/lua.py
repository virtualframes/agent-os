"""Lua executor implementation."""
from __future__ import annotations

from typing import Iterable

from .base import BaseExecutor


class LuaExecutor(BaseExecutor):
    """Execute Lua snippets using ``lua``."""

    language = "lua"

    @property
    def command(self) -> Iterable[str] | str:
        return ["lua"]

    @property
    def file_extension(self) -> str:
        return "lua"


__all__ = ["LuaExecutor"]
