"""Registry for language executor plugins."""
from __future__ import annotations

from typing import Dict, Iterable, Optional, Type

from .base import BaseExecutor
from .bash import BashExecutor
from .go import GoExecutor
from .javascript import JavaScriptExecutor
from .lua import LuaExecutor
from .php import PHPExecutor
from .python import PythonExecutor
from .ruby import RubyExecutor
from .rust import RustExecutor
from .typescript import TypeScriptExecutor


class ExecutorRegistry:
    """Manage executor instances keyed by language identifier."""

    def __init__(self) -> None:
        self._executors: Dict[str, BaseExecutor] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        for executor_cls in self._default_executor_classes():
            self.register(executor_cls())

    @staticmethod
    def _default_executor_classes() -> Iterable[Type[BaseExecutor]]:
        return (
            PythonExecutor,
            JavaScriptExecutor,
            TypeScriptExecutor,
            RustExecutor,
            GoExecutor,
            BashExecutor,
            LuaExecutor,
            RubyExecutor,
            PHPExecutor,
        )

    def register(self, executor: BaseExecutor) -> None:
        self._executors[executor.language.lower()] = executor

    def get(self, language: str) -> Optional[BaseExecutor]:
        return self._executors.get(language.lower())

    def available_languages(self) -> Iterable[str]:
        return sorted(self._executors.keys())


executor_registry = ExecutorRegistry()


__all__ = ["ExecutorRegistry", "executor_registry"]
