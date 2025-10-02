"""Abstract base classes for persistent language REPLs."""
from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Optional

import pexpect


class BaseREPL(ABC):
    """Manage a persistent read-eval-print loop for a language."""

    encoding: str = "utf-8"

    def __init__(self, prompt: str) -> None:
        self.prompt = prompt
        self.process: Optional[pexpect.spawn] = None
        self.session_id = str(uuid.uuid4())

    @property
    @abstractmethod
    def language(self) -> str:
        """Language identifier handled by the REPL."""

    @property
    @abstractmethod
    def command(self) -> str:
        """Command used to spawn the REPL."""

    def spawn_kwargs(self) -> dict:
        return {}

    async def start(self) -> None:
        if self.process is not None and self.process.isalive():
            return

        self.process = pexpect.spawn(
            self.command,
            encoding=self.encoding,
            timeout=None,
            echo=False,
            **self.spawn_kwargs(),
        )
        await asyncio.to_thread(self.process.expect_exact, self.prompt)

    async def eval(self, code: str) -> str:
        if self.process is None or not self.process.isalive():
            await self.start()

        assert self.process is not None
        await asyncio.to_thread(self.process.sendline, code)
        await asyncio.to_thread(self.process.expect_exact, self.prompt)
        raw = (self.process.before or "").replace("\r\n", "\n")
        return raw.strip()

    async def reset(self) -> None:
        self.stop()
        await self.start()

    def stop(self) -> None:
        if self.process is not None:
            self.process.close(force=True)
            self.process = None

    def __del__(self) -> None:  # pragma: no cover - defensive cleanup
        try:
            self.stop()
        except Exception:
            pass


__all__ = ["BaseREPL"]
