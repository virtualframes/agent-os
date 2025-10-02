"""Persistent interactive shell management for Agent-OS."""

from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator, Optional

import pexpect


class InteractiveShell:
    """Maintain a long-running shell session with asynchronous access."""

    def __init__(
        self,
        shell_type: str = "bash",
        prompt: str = "AGENT_OS> ",
    ) -> None:
        self.shell_type = shell_type
        self.prompt = prompt
        self.process: Optional[pexpect.spawn] = None
        self.cwd = os.getcwd()

    async def start(self) -> None:
        """Spawn the interactive shell if it is not already running."""

        if self.process is not None and self.process.isalive():
            return

        self.process = pexpect.spawn(
            self.shell_type,
            timeout=None,
            encoding="utf-8",
            echo=False,
            cwd=self.cwd,
        )

        await asyncio.to_thread(
            self.process.sendline, f'export PS1="{self.prompt}"'
        )
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


__all__ = ["InteractiveShell"]
