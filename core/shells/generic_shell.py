"""Fallback shell implementation for arbitrary shell commands."""
from __future__ import annotations

from .base import BaseShell


class GenericShell(BaseShell):
    """Spawn any shell command while reusing :class:`BaseShell` plumbing."""

    def __init__(self, command: str, prompt: str = "AGENT_OS> ") -> None:
        super().__init__(prompt=prompt)
        self._command = command

    @property
    def shell_type(self) -> str:
        return self._command

    @property
    def command(self) -> str:
        return self._command


__all__ = ["GenericShell"]
