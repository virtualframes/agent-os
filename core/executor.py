"""Facade for language-specific executors."""
from __future__ import annotations

from typing import AsyncIterator, Dict, Optional

from .executors import ExecutorRegistry, executor_registry


class LanguageExecutor:
    """Dispatch code execution to language-specific executors.

    The facade preserves the previous public API while delegating the heavy
    lifting to dedicated executor implementations housed under
    :mod:`core.executors`.
    """

    def __init__(self, registry: Optional[ExecutorRegistry] = None) -> None:
        self.registry = registry or executor_registry

    async def execute(
        self,
        code: str,
        language: str,
        *,
        stdin: Optional[str] = None,
        working_directory: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> AsyncIterator[str]:
        executor = self.registry.get(language)
        if executor is None:
            yield f"Error: language '{language}' is not supported.\n"
            return

        async for chunk in executor.execute_stream(
            code,
            stdin=stdin,
            working_directory=working_directory,
            env=env,
        ):
            yield chunk

    async def terminate(self, language: str | None = None) -> None:
        """Terminate running executors.

        If *language* is ``None`` all registered executors are terminated.
        """

        if language is not None:
            executor = self.registry.get(language)
            if executor is not None:
                await executor.terminate()
            return

        for lang in self.registry.available_languages():
            executor = self.registry.get(lang)
            if executor is not None:
                await executor.terminate()


__all__ = ["LanguageExecutor"]
