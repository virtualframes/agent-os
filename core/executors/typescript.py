"""TypeScript executor backed by Deno."""
from __future__ import annotations

from typing import Iterable

from .base import BaseExecutor


class TypeScriptExecutor(BaseExecutor):
    """Execute TypeScript via ``deno run``."""

    language = "typescript"

    @property
    def command(self) -> Iterable[str] | str:
        return ["deno", "run"]

    @property
    def file_extension(self) -> str:
        return "ts"


__all__ = ["TypeScriptExecutor"]
