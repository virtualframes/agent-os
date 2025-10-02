"""Python REPL implementation."""
from __future__ import annotations

from .base import BaseREPL


class PythonREPL(BaseREPL):
    language = "python"

    def __init__(self) -> None:
        super().__init__(prompt=">>> ")

    @property
    def command(self) -> str:
        return "python3"


__all__ = ["PythonREPL"]
