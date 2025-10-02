"""Node.js REPL implementation."""
from __future__ import annotations

from .base import BaseREPL


class NodeREPL(BaseREPL):
    language = "node"

    def __init__(self) -> None:
        super().__init__(prompt="> ")

    @property
    def command(self) -> str:
        return "node"


__all__ = ["NodeREPL"]
