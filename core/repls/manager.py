"""REPL manager orchestrating language-specific implementations."""
from __future__ import annotations

from typing import Dict, Type

from .base import BaseREPL
from .lua_repl import LuaREPL
from .node_repl import NodeREPL
from .python_repl import PythonREPL


class REPLManager:
    """Create and cache persistent REPL sessions."""

    def __init__(self) -> None:
        self._repl_types: Dict[str, Type[BaseREPL]] = {
            "python": PythonREPL,
            "node": NodeREPL,
            "lua": LuaREPL,
        }
        self._instances: Dict[str, BaseREPL] = {}

    def register(self, repl_cls: Type[BaseREPL]) -> None:
        self._repl_types[repl_cls.language.lower()] = repl_cls

    async def get_repl(self, language: str) -> BaseREPL:
        lang = language.lower()
        if lang not in self._repl_types:
            raise ValueError(f"No REPL available for language '{language}'")

        repl = self._instances.get(lang)
        if repl is None or repl.process is None or not repl.process.isalive():
            repl = self._repl_types[lang]()
            await repl.start()
            self._instances[lang] = repl

        return repl

    async def eval(self, language: str, code: str) -> str:
        repl = await self.get_repl(language)
        return await repl.eval(code)

    def stop(self, language: str | None = None) -> None:
        if language is None:
            for repl in list(self._instances.values()):
                repl.stop()
            self._instances.clear()
            return

        lang = language.lower()
        repl = self._instances.pop(lang, None)
        if repl is not None:
            repl.stop()


__all__ = ["REPLManager"]
