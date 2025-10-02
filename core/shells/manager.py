"""Shell manager coordinating persistent shell sessions."""
from __future__ import annotations

from typing import Dict, Optional, Type

from .base import BaseShell
from .bash_shell import BashShell
from .generic_shell import GenericShell
from .zsh_shell import ZshShell


class ShellManager:
    """Factory and lifecycle manager for interactive shell sessions."""

    def __init__(self) -> None:
        self._shell_types: Dict[str, Type[BaseShell]] = {
            "bash": BashShell,
            "zsh": ZshShell,
        }
        self._sessions: Dict[str, BaseShell] = {}

    def register(self, shell_type: str, shell_cls: Type[BaseShell]) -> None:
        self._shell_types[shell_type.lower()] = shell_cls

    async def create_session(self, shell_type: str = "bash", prompt: str = "AGENT_OS> ") -> BaseShell:
        shell_cls = self._shell_types.get(shell_type.lower())
        if shell_cls is None:
            shell = GenericShell(command=shell_type, prompt=prompt)
        else:
            shell = shell_cls(prompt=prompt)
        await shell.start()
        self._sessions[shell.session_id] = shell
        return shell

    def get_session(self, session_id: str) -> Optional[BaseShell]:
        return self._sessions.get(session_id)

    async def close_session(self, session_id: str) -> None:
        shell = self._sessions.pop(session_id, None)
        if shell is not None:
            shell.stop()

    async def close_all(self) -> None:
        for session_id in list(self._sessions.keys()):
            await self.close_session(session_id)

    def available_shells(self) -> list[str]:
        return sorted(self._shell_types.keys())


__all__ = ["ShellManager"]
