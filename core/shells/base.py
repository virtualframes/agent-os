"""Abstract base classes for persistent interactive shells."""
from __future__ import annotations

import asyncio
import os
import uuid
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

import pexpect


class BaseShell(ABC):
    """Manage a long-running interactive shell session."""

    encoding: str = "utf-8"

    def __init__(self, prompt: str = "AGENT_OS> ") -> None:
        self.prompt = prompt
        self.process: Optional[pexpect.spawn] = None
        self.cwd = os.getcwd()
        self.session_id = str(uuid.uuid4())

    @property
    @abstractmethod
    def shell_type(self) -> str:
        """Human readable shell identifier."""

    @property
    @abstractmethod
    def command(self) -> str:
        """Command used to spawn the shell."""

    def spawn_kwargs(self) -> dict:
        """Additional keyword arguments passed to ``pexpect.spawn``."""

        return {}

    async def start(self) -> None:
        """Spawn the shell process if it is not already running."""

        if self.process is not None and self.process.isalive():
            return

        self.process = pexpect.spawn(
            self.command,
            timeout=None,
            encoding=self.encoding,
            echo=False,
            cwd=self.cwd,
            **self.spawn_kwargs(),
        )

        await asyncio.to_thread(self.process.sendline, f'export PS1="{self.prompt}"')
        await asyncio.to_thread(self.process.expect_exact, self.prompt)

    async def execute(self, command: str) -> AsyncIterator[str]:
        """Execute *command* within the persistent shell."""

        if self.process is None or not self.process.isalive():
            await self.start()

        assert self.process is not None
        await asyncio.to_thread(self.process.sendline, command)

        try:
            output = await asyncio.to_thread(self._collect_until_prompt)
        except pexpect.EOF:
            output = (self.process.before or "").replace("\r\n", "\n")
            self.stop()

        for chunk in output.splitlines(keepends=True):
            if chunk:
                yield chunk

        if self.process is not None:
            await self._update_cwd()

    async def _update_cwd(self) -> None:
        if self.process is None or not self.process.isalive():
            return

        await asyncio.to_thread(self.process.sendline, "pwd")
        try:
            await asyncio.to_thread(self.process.expect_exact, self.prompt)
        except pexpect.EOF:
            self.stop()
            return
        raw = (self.process.before or "").strip()
        if raw:
            self.cwd = raw.splitlines()[-1]

    def stop(self) -> None:
        """Terminate the shell session."""

        if self.process is not None:
            self.process.close(force=True)
            self.process = None

    def __del__(self) -> None:  # pragma: no cover - defensive cleanup
        try:
            self.stop()
        except Exception:
            pass

    def _collect_until_prompt(self) -> str:
        assert self.process is not None
        self.process.expect_exact(self.prompt)
        raw = self.process.before
        return raw.replace("\r\n", "\n")


__all__ = ["BaseShell"]
