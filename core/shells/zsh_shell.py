"""Zsh shell implementation."""
from __future__ import annotations

from .base import BaseShell


class ZshShell(BaseShell):
    shell_type = "zsh"

    @property
    def command(self) -> str:
        return "zsh"


__all__ = ["ZshShell"]
