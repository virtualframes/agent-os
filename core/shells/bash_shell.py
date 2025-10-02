"""Bash shell implementation."""
from __future__ import annotations

from .base import BaseShell


class BashShell(BaseShell):
    shell_type = "bash"

    @property
    def command(self) -> str:
        return "bash"


__all__ = ["BashShell"]
