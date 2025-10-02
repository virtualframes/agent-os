"""Language-specific REPL management utilities."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict

import pexpect


@dataclass
class REPLConfig:
    command: str
    prompt: str


class REPLManager:
    """Create and manage persistent REPL sessions for multiple languages."""

    SUPPORTED: Dict[str, REPLConfig] = {
        "python": REPLConfig(command="python3", prompt=">>> "),
        "node": REPLConfig(command="node", prompt="> "),
        "lua": REPLConfig(command="lua", prompt="> "),
    }

    def __init__(self) -> None:
        self.repls: Dict[str, pexpect.spawn] = {}

    async def get_repl(self, language: str) -> pexpect.spawn:
        """Return a running REPL for *language*, creating it if needed."""

        language = language.lower()
        if language not in self.SUPPORTED:
            raise ValueError(f"No REPL available for language '{language}'")

        if language in self.repls and self.repls[language].isalive():
            return self.repls[language]

        config = self.SUPPORTED[language]
        repl = pexpect.spawn(
            config.command,
            encoding="utf-8",
            timeout=None,
            echo=False,
        )
        await asyncio.to_thread(repl.expect_exact, config.prompt)
        self.repls[language] = repl
        return repl

    async def eval(self, language: str, code: str) -> str:
        """Evaluate *code* in the REPL for *language* and return the output."""

        repl = await self.get_repl(language)
        config = self.SUPPORTED[language]

        await asyncio.to_thread(repl.sendline, code)
        await asyncio.to_thread(repl.expect_exact, config.prompt)
        raw = repl.before.replace("\r\n", "\n")
        return raw.strip()

    def stop(self, language: str | None = None) -> None:
        """Stop a single REPL or all managed REPLs."""

        if language is None:
            for repl in list(self.repls.values()):
                repl.close(force=True)
            self.repls.clear()
            return

        lang = language.lower()
        repl = self.repls.get(lang)
        if repl is not None:
            repl.close(force=True)
            del self.repls[lang]

    def __del__(self) -> None:  # pragma: no cover - defensive cleanup
        try:
            self.stop()
        except Exception:
            pass


__all__ = ["REPLManager", "REPLConfig"]
