"""Compatibility layer for interactive shell sessions."""
from __future__ import annotations

from typing import AsyncIterator, Dict, Type

from .shells import BaseShell, BashShell, ShellManager, ZshShell


_SHELL_TYPES: Dict[str, Type[BaseShell]] = {
    "bash": BashShell,
    "zsh": ZshShell,
}


class InteractiveShell:
    """Backward-compatible wrapper around the new shell architecture."""

    def __init__(self, shell_type: str = "bash", prompt: str = "AGENT_OS> ") -> None:
        self.shell_type = shell_type
        self.prompt = prompt
        shell_cls = _SHELL_TYPES.get(shell_type.lower())
        if shell_cls is None:
            raise ValueError(f"Unsupported shell type '{shell_type}'")
        self._shell = shell_cls(prompt=prompt)

    async def start(self) -> None:
        await self._shell.start()

    async def execute(self, command: str) -> AsyncIterator[str]:
        async for chunk in self._shell.execute(command):
            yield chunk

    def stop(self) -> None:
        self._shell.stop()

    @property
    def session_id(self) -> str:
        return self._shell.session_id


__all__ = ["InteractiveShell", "ShellManager", "BaseShell", "BashShell", "ZshShell"]
